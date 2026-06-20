# Changelog

## [0.3.0](https://github.com/jegor377/mlops-project/compare/frontend@0.2.2...frontend@0.3.0) (2026-06-20)


### Features

* **auth:** adds is_active to auth context ([66aba1d](https://github.com/jegor377/mlops-project/commit/66aba1da7710920bb69297733758fb2adb5ffb09))
* **auth:** prevent deactivated users from signing in via Google ([0c697a0](https://github.com/jegor377/mlops-project/commit/0c697a0e4e595c5159e665e05d0adf9ecdf1fa9b))
* **dashboard:** adds ability to create PATs in dashboard ([d939190](https://github.com/jegor377/mlops-project/commit/d9391900a855e1515c51d3cf96152971d51524e7))
* **dashboard:** adds ability to go from overview to requests page ([bf6657d](https://github.com/jegor377/mlops-project/commit/bf6657d0c7d6e4036172f5d61f8c6d111d2d7f90))
* **dashboard:** adds audit log section ([e6f1c01](https://github.com/jegor377/mlops-project/commit/e6f1c017291b11f46a1ce86d05d64581cf6b40cd))
* **dashboard:** adds overview and requests log implementation ([e03356a](https://github.com/jegor377/mlops-project/commit/e03356a075b6d35cd216e3d5d4e11acd09f8fd8c))
* **dashboard:** adds resend account verification email btn and blocks fetching PATs data if user is inactive ([a83b827](https://github.com/jegor377/mlops-project/commit/a83b82792cb89bebdfbca6d7abb0d7833b0dff87))
* **dashboard:** allows to send create PAT request to ml_server ([02b24be](https://github.com/jegor377/mlops-project/commit/02b24be793f99bf86e968579fb95b19e0f18a5a9))
* **dashboard:** handles paging and adds showing revoked_at info ([ecfd916](https://github.com/jegor377/mlops-project/commit/ecfd9168a7f1425c9e9b2b408e3c83479677c72f))
* **frontend:** adds forgot-password and reset-password pages ([5993321](https://github.com/jegor377/mlops-project/commit/5993321ce947df72b86ec4ff2064c9eabf552e55))
* **frontend:** implements classic login route handling ([7126ffa](https://github.com/jegor377/mlops-project/commit/7126ffa9961c06ff8b37fbcc9d3ca5424f41d6db))
* **frontend:** working get started page ([39b8a5a](https://github.com/jegor377/mlops-project/commit/39b8a5a88ef41ac1d2e8e87afe57215468d75c66))
* **login:** adds "account activated" message after navigating to account verification link ([735df56](https://github.com/jegor377/mlops-project/commit/735df56235ec26f70308f717ac19be008a43cc50))
* **login:** adds github login button handling ([34afbdc](https://github.com/jegor377/mlops-project/commit/34afbdc384e2167ae281954da705fbdfcff5348c))
* **login:** handle login via google and adds on google login cancelled warning banner ([1712ab5](https://github.com/jegor377/mlops-project/commit/1712ab5e23ae17955d2a024622f91fab2c1d90b5))
* **nav:** adds logout and auth context for session handling ([bdbddba](https://github.com/jegor377/mlops-project/commit/bdbddbac88bc8ae65ec7982d138a390ab6c46076))
* **register:** adds github login button handling ([b8fa87f](https://github.com/jegor377/mlops-project/commit/b8fa87fb57baf4039b4b81265c43c7cd77d6941e))
* **register:** adds login via google to register route ([0e45bc1](https://github.com/jegor377/mlops-project/commit/0e45bc16f242bbddc10c0269e0b392c1415bcd97))


### Bug Fixes

* **auth:** fixes not refetching /me after loging in bug ([e03e1c7](https://github.com/jegor377/mlops-project/commit/e03e1c7c2b697efd30bf2637a58fa440f99960f9))
* **dashboard:** ads proper cursor-pointer class instead of LLM generated dots ([f6e19b4](https://github.com/jegor377/mlops-project/commit/f6e19b4b48b1838d1c6d5d4dd2183e11db42da90))
* **dashboard:** fixes audit log endpoint url bug ([fb8507d](https://github.com/jegor377/mlops-project/commit/fb8507dfef0b63360e40330b0b284f71b05fc11b))
* **dashboard:** fixes not showing activate account message on first login ([4f87233](https://github.com/jegor377/mlops-project/commit/4f87233a685aaab002f90b97003871c32f29a1e5))
* **login:** fixes autofill bug when login and password have been already saved in the browser ([0f551cc](https://github.com/jegor377/mlops-project/commit/0f551cc9f84a9aff6f254663847a8e9b00ea0ee0))

## [0.2.2](https://github.com/jegor377/mlops-project/compare/frontend@0.2.1...frontend@0.2.2) (2026-04-03)


### Bug Fixes

* **frontend:** ci frontend test ([33e9c0a](https://github.com/jegor377/mlops-project/commit/33e9c0a3417256452d7f3fd74903bba7f9b3417f))

## [0.2.1](https://github.com/jegor377/mlops-project/compare/frontend@0.2.0...frontend@0.2.1) (2026-04-02)


### Bug Fixes

* **frontend:** frontend ci test ([28c914b](https://github.com/jegor377/mlops-project/commit/28c914b3e74adea48da5e6b94ea90e706795fd68))
* **frontend:** frontend ci test ([e7a4370](https://github.com/jegor377/mlops-project/commit/e7a4370ada8c2f050970ac7c16eb746fb5425360))

## [0.2.0](https://github.com/jegor377/mlops-project/compare/frontend@0.1.0...frontend@0.2.0) (2026-03-28)


### Features

* **frontend:** adds frontend app ([4832fcd](https://github.com/jegor377/mlops-project/commit/4832fcdbfad7ce5f1a74657877062e0dc11ec3e4))
