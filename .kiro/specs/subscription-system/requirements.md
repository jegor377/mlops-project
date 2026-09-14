# Requirements Document

## Introduction

Volta currently has database models and services for billing/subscription management, but the system is not fully operational. The checkout flow fails because the Pro plan is not seeded in the database, and there is no mechanism to ensure default plans exist. This feature implements the subscription system integration to enable users to subscribe to different plans (Free, Pro) and manage their subscription state through Stripe.

## Glossary

- **System**: Volta - the ML inference API platform
- **Plan**: A subscription tier with specific features and limits (Free, Pro, Enterprise/Custom)
- **Subscription**: An active agreement between a user and the System to use a specific Plan
- **Stripe**: Third-party payment processing service
- **Pro Plan**: The paid subscription tier with enhanced features
- **Free Plan**: The free subscription tier with basic features
- **Enterprise/Custom Plan**: A negotiated plan for large organizations with custom features
- **Checkout Session**: Stripe's hosted payment page for subscription creation
- **Webhook**: Stripe's HTTP callback for event notifications

## Requirements

### Requirement 1: Seed Default Plans

**User Story:** As a platform operator, I want the default plans (Free, Pro) to be automatically seeded into the database on startup, so that users can immediately subscribe without manual database setup.

#### Acceptance Criteria

1. WHEN the System starts up, THE System SHALL check if the Free Plan exists in the database
2. IF the Free Plan does not exist, THE System SHALL create it with default limits (unlimited requests_per_day, api_key_limit, history_days)
3. WHEN the System starts up, THE System SHALL check if the Pro Plan exists in the database
4. IF the Pro Plan does not exist AND stripe_price_id is configured via settings, THE System SHALL create the Pro Plan with the configured stripe_price_id
5. IF the Pro Plan exists but stripe_price_id is NULL, THE System SHALL update it with the configured stripe_price_id

### Requirement 2: Complete Checkout Flow

**User Story:** As a user, I want to complete the subscription checkout flow through Stripe, so that I can upgrade from the Free plan to the Pro plan.

#### Acceptance Criteria

1. WHEN a user clicks "Subscribe" from the billing page, THE System SHALL create a Stripe checkout session for the Pro Plan
2. WHEN the System creates a checkout session, THE System SHALL include the user_id in the session metadata
3. WHEN the System creates a checkout session, THE System SHALL set success_url to the billing success page
4. WHEN the System creates a checkout session, THE System SHALL set cancel_url to the billing cancel page
5. WHEN the Stripe checkout session URL is returned, THE System SHALL redirect the user to that URL
6. IF a user already has a pending checkout, THE System SHALL return an error indicating checkout is in progress

### Requirement 3: Synchronize Subscription State from Stripe

**User Story:** As the System, I want to synchronize subscription state from Stripe webhooks, so that the local subscription status always reflects the Stripe status.

#### Acceptance Criteria

1. WHEN the System receives a checkout.session.completed webhook from Stripe, THE System SHALL create or update the user's subscription
2. WHEN a subscription is created from a checkout.session.completed event, THE System SHALL set status to the Stripe status mapped to local status
3. WHEN a subscription is created from a checkout.session.completed event, THE System SHALL set current_period_end to the Stripe period end timestamp
4. WHEN the System receives a customer.subscription.updated webhook from Stripe, THE System SHALL update the local subscription status
5. WHEN the System receives a customer.subscription.deleted webhook from Stripe, THE System SHALL set the subscription status to CANCELED and record canceled_at timestamp
6. IF a webhook event references a user or subscription that does not exist, THE System SHALL log an error and continue processing other events

### Requirement 4: Fallback to Free Plan

**User Story:** As a user whose subscription ends, I want to automatically fall back to the Free plan, so that I can continue using the service without interruption.

#### Acceptance Criteria

1. WHEN a subscription's status changes to CANCELED, THE System SHALL NOT automatically downgrade the user
2. WHILE a user has no active subscription, THE System SHALL continue to enforce Free plan limits (daily_request_limit from settings)
3. WHERE a user has an expired subscription, THE System SHALL allow them to renew by starting a new checkout flow

### Requirement 5: Upgrade Subscription

**User Story:** As a user, I want to upgrade my current subscription to Pro, so that I can access additional features and higher usage limits.

#### Acceptance Criteria

1. WHEN a user with an active subscription clicks "Upgrade", THE System SHALL create a Stripe checkout session for the Pro Plan
2. WHEN the System creates a checkout session for upgrade, THE System SHALL set subscription_data[metadata][user_id] to the current user ID
3. WHEN the System creates a checkout session for upgrade, THE System SHALL set subscription_data[metadata][current_subscription_id] to the existing subscription Stripe ID
4. WHEN the Stripe checkout session completes for an upgrade, THE System SHALL update the existing subscription to point to the new Pro plan
5. IF a user with a CANCELED subscription clicks "Subscribe", THE System SHALL create a new subscription (not update the canceled one)

### Requirement 6: Contact Sales

**User Story:** As a user interested in a custom plan, I want to be able to submit a contact sales form, so that the sales team can reach out to discuss a custom Enterprise solution.

#### Acceptance Criteria

1. WHEN a user submits the contact sales form, THE System SHALL send an email notification to the configured sales email address
2. WHEN sending the email, THE System SHALL include the user name, email, company name, message, and current plan tier
3. WHEN the form submission is successful, THE System SHALL return a success response to the user
4. IF the email sending fails, THE System SHALL return an error response without revealing email configuration details

### Requirement 7: View Current Subscription

**User Story:** As a user, I want to view my current subscription status, so that I can see which plan I am on and when it renews.

#### Acceptance Criteria

1. WHEN a user requests their subscription status, THE System SHALL return the subscription details including plan name, status, current_period_start, and current_period_end
2. IF a user has no active subscription, THE System SHALL return a subscription object with status CANCELED and no plan details
