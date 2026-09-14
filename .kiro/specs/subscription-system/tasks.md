# Implementation Plan: Subscription System

## Overview

This implementation adds a complete subscription management system for Volta. The system enables users to subscribe to different plan tiers (Free, Pro, Enterprise/Custom) through Stripe payment processing with automatic synchronization of subscription state.

The implementation addresses all 7 requirements:
1. **Seed Default Plans** - Auto-create Free/Pro plans on startup
2. **Complete Checkout Flow** - Stripe checkout for Free→Pro upgrade
3. **Synchronize Subscription State** - Stripe webhook sync
4. **Fallback to Free Plan** - Auto-enforce Free limits when subscription ends
5. **Upgrade Subscription** - Handle existing subscriber upgrades
6. **View Current Subscription** - Endpoint to see subscription status

This document breaks down the implementation into discrete coding steps based on the requirements and design documents.

## Tasks

- [x] 1. Implement plan seeding mechanism (requirements 1)
  - [x] 1.1 Add seed_default_plans() function to billing.py service
    - Check if Free plan exists, create if missing with default limits (unlimited requests_per_day, api_key_limit, history_days)
    - Check if Pro plan exists, create if missing with configured stripe_price_id
    - Update Pro plan's stripe_price_id if it exists but is NULL
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 1.2 Write property test for plan seeding idempotence
    - **Property 1: Plan Seeding Idempotence**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    - Test that running seed mechanism N times produces exactly 1 Free + 1 Pro plan

- [x] 2. Update checkout service for upgrade flows (requirements 2, 5)
  - [x] 2.1 Update create_upgrade_checkout_session() in billing.py service
    - Get Pro plan from database
    - Ensure Stripe customer exists for user
    - Build line items for Pro plan
    - If user has existing subscription with Stripe ID, create upgrade session with subscription_data metadata
    - If no existing subscription, create standard session
    - Return Stripe checkout session
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3_

- [x] 3. Add new /checkout/upgrade endpoint (requirements 2, 5)
  - [x] 3.1 Add POST /checkout/upgrade endpoint to checkout.py routes
    - Set user.pending_checkout=True
    - Get Pro plan from database (raise error if not configured)
    - Ensure Stripe customer exists for user
    - Get existing subscription (if any) for upgrade metadata
    - Call create_upgrade_checkout_session() to create Stripe session
    - Commit changes and redirect to Stripe
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 5.1, 5.2, 5.3_
  
  - [ ]* 3.2 Write unit tests for upgrade endpoint
    - Test successful upgrade checkout creation with existing subscription
    - Test successful upgrade checkout creation without existing subscription
    - Test error when Pro plan not configured
    - Test error when user has pending checkout
    - _Requirements: 2.6_

- [x] 4. Update webhook handler for upgrade flows (requirements 3, 4)
  - [x] 4.1 Update handle_checkout_session_completed() in billing.py
    - Extract is_upgrade flag from checkout session metadata
    - If is_upgrade=true and existing subscription found, update subscription to Pro plan
    - If is_upgrade=false or no existing subscription, create new subscription
    - Set user.pending_checkout=False in both cases
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 5. Add billing subscription endpoint (requirements 7)
  - [ ] 5.1 Create new /billing/subscription GET endpoint in billing.py routes
    - Query user's subscription with plan eager loading
    - Return canceled status if no subscription or CANCELED status
    - Return subscription details (status, period dates, plan info) if active
    - _Requirements: 7.1, 7.2_

- [ ] 6. Integrate plan seeding into application startup (requirements 1)
  - [ ] 6.1 Update lifespan() in app.py to seed default plans
    - Create async session
    - Call seed_default_plans() with session and settings
    - Handle any seeding errors gracefully
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 7. Implement frontend dashboard integration (requirements 2, 5, 7)
  - [ ] 7.1 Add billing tab to dashboard sidebar
    - Ensure "billing" NavId exists in NAV array (already present)
    - Verify billing icon is defined in icons object (already present)
    - _Requirements: 2.1, 5.1, 7.1_
  
  - [ ] 7.2 Add billing page component to dashboard
    - Create BillingPage component with subscription status display
    - Fetch subscription status from /api/billing/subscription endpoint
    - Display plan tier, status, period dates
    - Add "Upgrade to Pro" button that calls POST /checkout/upgrade
    - Handle pending checkout banner (already implemented in PendingCheckoutBanner)
    - _Requirements: 2.1, 5.1, 7.1, 7.2_
  
  - [ ] 7.3 Wire billing page into dashboard routing
    - Add billing case to content Partial<Record<NavId, ReactNode>> mapping
    - Set active="billing" in Sidebar to render billing page
    - _Requirements: 2.1, 5.1, 7.1_

- [ ] 8. Write property tests for upgrade flows (Property 2, 3, 4, 5, 6, 7, 8)
  - [ ]* 8.1 Write property test for checkout session uniqueness (Property 2)
    - **Property 2: Checkout Session Uniqueness**
    - **Validates: Requirements 2.6**
    - Test that creating new checkout fails while pending_checkout=True
  
  - [ ]* 8.2 Write property test for subscription status synchronization (Property 3)
    - **Property 3: Subscription Status Synchronization**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    - Test that webhook events accurately reflect Stripe subscription status
  
  - [ ]* 8.3 Write property test for Free plan limit enforcement (Property 4)
    - **Property 4: Free Plan Limit Enforcement**
    - **Validates: Requirements 4.2**
    - Test that users with CANCELED subscription have Free limits enforced
  
  - [ ]* 8.4 Write property test for upgrade subscription preservation (Property 5, 7)
    - **Property 5: Upgrade Subscription Preservation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    - Test that upgrade updates existing subscription, not duplicate
  
  - [ ]* 8.5 Write property test for upgrade checkout session creation (Property 6)
    - **Property 6: Upgrade Checkout Session Creation**
    - **Validates: Requirements 2.7**
    - Test that clicking upgrade sets pending_checkout=True and creates session
  
  - [ ]* 8.6 Write property test for canceled subscription renewal (Property 8)
    - **Property 8: Canceled Subscription Renewal**
    - **Validates: Requirements 5.5**
    - Test that canceled subscription creates new subscription on checkout

- [ ] 9. Write integration tests for complete workflows (requirements 1-7)
  - [ ] 9.1 Integration test for plan seeding (requirements 1)
    - Start app with no plans in database
    - Verify Free and Pro plans are created on startup
    - Restart app and verify no duplicate plans created
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 9.2 Integration test for upgrade subscription flow (requirements 2, 3, 4, 5)
    - Create existing subscription (Free plan)
    - Call POST /checkout/upgrade
    - Verify pending_checkout=True
    - Verify upgrade checkout session created with correct metadata
    - Simulate Stripe webhook (checkout.session.completed with is_upgrade=true)
    - Verify subscription updated to Pro (not duplicated)
    - Verify user.pending_checkout=False
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 9.3 Integration test for upgrade without existing subscription (requirements 2, 3, 4)
    - Create user with no subscription
    - Call POST /checkout/upgrade
    - Verify pending_checkout=True
    - Verify checkout session created for Free plan
    - Simulate Stripe webhook
    - Verify new subscription created
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [ ] 9.4 Integration test for billing subscription endpoint (requirements 7)
    - Create user with active subscription (Free plan)
    - Call GET /billing/subscription
    - Verify response includes subscription status, period dates, and plan details
    - Create user with CANCELED subscription
    - Call GET /billing/subscription
    - Verify response includes status="canceled" with no plan details
    - _Requirements: 7.1, 7.2_
  
  - [ ] 9.5 Integration test for upgrade with canceled subscription (requirements 5)
    - Create user with CANCELED subscription
    - Call POST /checkout/upgrade
    - Verify checkout session created for new subscription
    - Simulate Stripe webhook
    - Verify new subscription created (not updating canceled one)
    - _Requirements: 5.5_
  
  - [ ]* 9.6 Integration test for checkout flow with pending checkout error (requirements 2)
    - Create user with pending_checkout=True
    - Call POST /checkout/upgrade
    - Verify error response with "checkout in progress"
    - Cancel checkout with POST /checkout/cancel
    - Call POST /checkout/upgrade again
    - Verify successful checkout creation
    - _Requirements: 2.6_

- [ ] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The billing page component will use existing NAV structure and icons (already defined in frontend/app/routes/dashboard.tsx)
- The PendingCheckoutBanner component is already implemented for handling pending checkout UI state

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "6.1"] },
    { "id": 1, "tasks": ["1.2", "5.1"] },
    { "id": 2, "tasks": ["2.1", "3.1"] },
    { "id": 3, "tasks": ["3.2", "4.1", "7.1"] },
    { "id": 4, "tasks": ["7.2", "7.3"] },
    { "id": 5, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6"] },
    { "id": 6, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5"] },
    { "id": 7, "tasks": ["9.6"] },
    { "id": 8, "tasks": ["10"] }
  ]
}
```
