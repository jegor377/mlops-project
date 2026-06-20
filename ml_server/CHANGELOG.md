# Changelog

## [0.10.0](https://github.com/jegor377/mlops-project/compare/ml_server@0.9.3...ml_server@0.10.0) (2026-06-20)


### Features

* **audit-log:** adds audit log endpoint ([ba8085d](https://github.com/jegor377/mlops-project/commit/ba8085de643bddc25f615349818921bfd38675bb))
* **auth:** add is_active to me route ([a88d6cb](https://github.com/jegor377/mlops-project/commit/a88d6cbba72d0a767c98093d618dba895be47f26))
* **auth:** adds github oauth login backend routes ([3870a22](https://github.com/jegor377/mlops-project/commit/3870a229db6138af3efbafa2ac2c057646d33e0d))
* **auth:** adds logout endpoint ([96e2d7d](https://github.com/jegor377/mlops-project/commit/96e2d7df91b534f4844e03287d9f49d72f72bd0a))
* **auth:** adds oauth2 authorization code flow login via google ([de1acfd](https://github.com/jegor377/mlops-project/commit/de1acfd433685d70694c31fd9c324d8473cf14d0))
* **auth:** adds resend_verification route ([5cd19c5](https://github.com/jegor377/mlops-project/commit/5cd19c516e830d52a321555056daf6b196585ddb))
* **auth:** prevent deactivated users from signing in via Google ([0c697a0](https://github.com/jegor377/mlops-project/commit/0c697a0e4e595c5159e665e05d0adf9ecdf1fa9b))
* **general:** adds rate limitting the predict request and capturing the latest requests and its metrics ([7003e5e](https://github.com/jegor377/mlops-project/commit/7003e5eef0a0b1d3a042ab793eec17bad753d58e))
* **ml_server:** add user registration endpoint ([6e2fb9b](https://github.com/jegor377/mlops-project/commit/6e2fb9bdcc685d34f797186af07faf7a748d6d77))
* **ml_server:** adds classic login route to auth along with session management ([c4027a3](https://github.com/jegor377/mlops-project/commit/c4027a36d04a8711e856908483c1fb9a6e74e204))
* **ml_server:** adds email verification system to register endpoint ([090822f](https://github.com/jegor377/mlops-project/commit/090822f5f4896433430b3e6f6ce052c6f3f63d21))
* **ml_server:** adds endpoints, db models, db migration and schemas for forgot-password and reset-password ([3a83d8c](https://github.com/jegor377/mlops-project/commit/3a83d8c8587f146ba8a3aea801d306ae26656315))
* **pat:** adds pat endpoints to ml_server ([f328a80](https://github.com/jegor377/mlops-project/commit/f328a8043c42634ca5198ba3e425b6916e80e378))
* **pat:** adds revoked_at info and fixes PATStatus bug in list_pats ([8ad70db](https://github.com/jegor377/mlops-project/commit/8ad70db7fb11675d54fca5f828b07e73ec1fc502))
* **pat:** adds scopes and pat authorization dependency ([e16a287](https://github.com/jegor377/mlops-project/commit/e16a2874d7aebd969a9c72f90a1240d593bc2ac5))
* **pat:** adds sending email notifications on every pat creation and revoke ([1becc7f](https://github.com/jegor377/mlops-project/commit/1becc7fe1d105a6fde84b7d9d87402fea8de03c6))
* **requests:** adds requests stats endpoints ([b43adba](https://github.com/jegor377/mlops-project/commit/b43adba7c5fd711489e320a3aa9e3323032d7263))


### Bug Fixes

* **auth:** fixes not working login_with_google endpoint and callback ([f662bb5](https://github.com/jegor377/mlops-project/commit/f662bb5c067deb29b645b2c4df2b3eac89be1fb5))
* **email_service:** changes order of info in send_pat_creation_email and fixes bug ([c9d1fe6](https://github.com/jegor377/mlops-project/commit/c9d1fe63cf4cbf1a1a2fe63dc5822cebe9f724ff))
* fix incomplete profile from google naked message instead of redirect with info ([2f4b9b8](https://github.com/jegor377/mlops-project/commit/2f4b9b8440bc8cc1b698546246036c313f280e61))
* fix return bug and lint issue "Function is too complex (C901)" ([ce7f772](https://github.com/jegor377/mlops-project/commit/ce7f772652bf325eb47c2aa096700c49674b1a39))
* **ml_server:** fix missing import ([47d16bf](https://github.com/jegor377/mlops-project/commit/47d16bff7bb35a15be7644ecb08c04423f4b029b))
* **pat:** prevent inactive users from creating PATs ([61c8386](https://github.com/jegor377/mlops-project/commit/61c8386ca56dfc97860b7a7009a31772527ae5b6))
* **pat:** remove typo that made response to be a list ([72c215b](https://github.com/jegor377/mlops-project/commit/72c215b14cbce1904979acc3fcffcf1388dba8d4))


### Chores

* adds authlib for google oauth2 auth code flow and pydantic-settings for better settings impl ([748e6d0](https://github.com/jegor377/mlops-project/commit/748e6d017e8c24309895a15e1adfd2d7c375e2c2))
* adds oauth state session secret key used for logging via oauth in google and frontend hostname for local testing ([ef51c02](https://github.com/jegor377/mlops-project/commit/ef51c022379f203794a71d45dc3344cec3d00068))
* adds redis example conf ([6077c6c](https://github.com/jegor377/mlops-project/commit/6077c6ce0562d6caf620aee5727bead2f9219829))
* adds redis package ([cf7c2f6](https://github.com/jegor377/mlops-project/commit/cf7c2f64caa944e07a43178d16609beab2d19014))
* fill missing .env.example file fields ([4be563b](https://github.com/jegor377/mlops-project/commit/4be563be5bf17ef6a9815baf2afc9097a8298521))
* **migration:** adds new UserAuthMethod model migration ([a213d9d](https://github.com/jegor377/mlops-project/commit/a213d9db0541bc68349563df52b6df5bc6c30f66))
* **ml_server:** add alembic with async migrations setup ([e570887](https://github.com/jegor377/mlops-project/commit/e57088736632a6790202ab93d32268c784b96ac6))
* **ml_server:** add initial users table migration ([2543aec](https://github.com/jegor377/mlops-project/commit/2543aecf11dd7bdb05c0b2a26bb9be35f3da46c2))
* **ml_server:** adds ability to test a single test file ([0cef7da](https://github.com/jegor377/mlops-project/commit/0cef7da21b37a0f9d75d694f07ebdc65c33b8e8a))
* **ml_server:** adds fastapi-mail package for verification email sending ([b966cd6](https://github.com/jegor377/mlops-project/commit/b966cd6e4aa6bf759c987a15ee428fe20a56b093))
* **ml_server:** adds fastapi-mail package for verification email sending ([486ddf1](https://github.com/jegor377/mlops-project/commit/486ddf1b58c76d18dd6a972805a51677409510c7))
* **ml_server:** email verification system db migration ([7ba2899](https://github.com/jegor377/mlops-project/commit/7ba2899af653ccd0593362785873341802640f0e))
* **ml_server:** make new-migration task wait for keyboard input to set migration message ([cbe2dd2](https://github.com/jegor377/mlops-project/commit/cbe2dd229de556eb2b26d02aaf15cf220583ad70))
* **ml_server:** remove test comment ([3125663](https://github.com/jegor377/mlops-project/commit/3125663a351d942b9bf5174ac9fb0194ec2deae6))
* **ml_server:** update taskfile to work with new email verification system for registration endpoint ([9aeb106](https://github.com/jegor377/mlops-project/commit/9aeb10626b8721ed59ebda72d98e1438dc60cdcb))
* **pat:** adds db migration ([bd8343e](https://github.com/jegor377/mlops-project/commit/bd8343ef4c8eebbb9d5fa7225b7d6ff66d6d8857))
* updates env example to account for correct secrets location ([6d80dfd](https://github.com/jegor377/mlops-project/commit/6d80dfd5aafa24d5ecb0660d0c7f9c953ded84d9))
* updates env example to account for correct secrets location ([e4e8438](https://github.com/jegor377/mlops-project/commit/e4e84384099a3ef938e89e9c6e9c6d7914bdfaf0))

## [0.9.3](https://github.com/jegor377/mlops-project/compare/ml_server@0.9.2...ml_server@0.9.3) (2026-04-03)


### Bug Fixes

* **ml_server:** ci ml_server test ([8c13149](https://github.com/jegor377/mlops-project/commit/8c1314963daece33893504153da9257b35364d3b))

## [0.9.2](https://github.com/jegor377/mlops-project/compare/ml_server@0.9.1...ml_server@0.9.2) (2026-04-02)


### Bug Fixes

* **ml_server:** ml_server ci test ([e75c367](https://github.com/jegor377/mlops-project/commit/e75c36778e2199d31ef5b6ed8e6e7607207686c9))
* **ml_server:** ml_server ci test ([e56c14d](https://github.com/jegor377/mlops-project/commit/e56c14d05a88bef61116f78bda2279762c764522))
* **server:** ml_server ci test ([b8f5745](https://github.com/jegor377/mlops-project/commit/b8f574520ec64ecf17ca3777a38fdf87f2e46409))

## [0.9.1](https://github.com/jegor377/mlops-project/compare/ml_server@0.9.0...ml_server@0.9.1) (2026-04-02)


### Chores

* rename server to ml_server ([cc9935f](https://github.com/jegor377/mlops-project/commit/cc9935f338a803c44bbf2c1a00e7e9aa55f1df7a))

## [0.9.0](https://github.com/jegor377/mlops-project/compare/server@0.8.3...server@0.9.0) (2026-02-11)


### Features

* adds health endpoint ([b0e7433](https://github.com/jegor377/mlops-project/commit/b0e74337330d6a44f3ddd5c97450ee87670f51f5))


### Bug Fixes

* **server:** fix utils taskfile ([68e8a21](https://github.com/jegor377/mlops-project/commit/68e8a2169abb07b9f1dc8f65b90fbdb370c59ba1))
* **server:** fixes ci git push ([2c87b29](https://github.com/jegor377/mlops-project/commit/2c87b29e02ab242151679e302013a000adc522e0))
* **server:** fixes ci image version update ([ce50a31](https://github.com/jegor377/mlops-project/commit/ce50a3151f30eb7b8bf9a8fb259c39516a1d2c14))

## [0.8.3](https://github.com/jegor377/mlops-project/compare/server@0.8.2...server@0.8.3) (2026-01-19)


### Bug Fixes

* **server:** fixes docker issue in server ([db9a2c4](https://github.com/jegor377/mlops-project/commit/db9a2c466652594a8736407716ea05c69df4150f))
* **server:** fixes docker issue in server ([2b67823](https://github.com/jegor377/mlops-project/commit/2b67823870da79afb9c6ab8d062c74d332ac8c3a))


### Chores

* upgrade uv ([1112423](https://github.com/jegor377/mlops-project/commit/111242337c6a537f52c14fb5f130d7f150a35b33))

## [0.8.2](https://github.com/jegor377/mlops-project/compare/server@0.8.1...server@0.8.2) (2026-01-14)


### Bug Fixes

* **server:** debug test ci ([14eb4a5](https://github.com/jegor377/mlops-project/commit/14eb4a5df7e19f360a1ba32b8d576c0bf47e0eb9))
* **server:** remove the test comment ([bcc7b7e](https://github.com/jegor377/mlops-project/commit/bcc7b7e38616b51527ac51efdd7d4e5828ba7e64))

## [0.8.1](https://github.com/jegor377/mlops-project/compare/server@0.8.0...server@0.8.1) (2026-01-14)


### Bug Fixes

* **server:** removes test comment ([5c55d87](https://github.com/jegor377/mlops-project/commit/5c55d8708f63a6a1aca048afc556c59bdf2ef524))

## [0.8.0](https://github.com/jegor377/mlops-project/compare/server@0.7.0...server@0.8.0) (2026-01-14)


### Features

* **server:** test release please change ([f1534d0](https://github.com/jegor377/mlops-project/commit/f1534d0536f656bb7191e7661aa87257e38ae59c))

## [0.7.0](https://github.com/jegor377/mlops-project/compare/server@0.6.0...server@0.7.0) (2026-01-11)


### Features

* **server:** remove the test ([c992041](https://github.com/jegor377/mlops-project/commit/c9920417bbc3a2f13331b05b4a5b7ccf8ab9fba8))


### Bug Fixes

* **server:** test ci ([f56ab3a](https://github.com/jegor377/mlops-project/commit/f56ab3a79a98d522750c7cd0f890b1f59a0ec7c4))

## [0.6.0](https://github.com/jegor377/mlops-project/compare/server@0.5.0...server@0.6.0) (2026-01-06)


### Features

* **server:** adds root endpoint ([e9c3814](https://github.com/jegor377/mlops-project/commit/e9c38145aa09dfba900224368a33d58bcb5bd1a8))
* **server:** adds root endpoint ([9a52e57](https://github.com/jegor377/mlops-project/commit/9a52e57b8ab78d2deefc9f90e0c8988a253747fd))


### Bug Fixes

* **ci:** fix ci ([73dab69](https://github.com/jegor377/mlops-project/commit/73dab69151feffca9583c4f625b5de9535c32a55))
* **ci:** fix ci error ([830136a](https://github.com/jegor377/mlops-project/commit/830136ab446485920e3e182d470b2200028f70b5))
* **server:** remove test msg ([b4a2dc5](https://github.com/jegor377/mlops-project/commit/b4a2dc592c2822d85de88297d1e5c1a15c59a8d7))
* **server:** test ([01d1cb9](https://github.com/jegor377/mlops-project/commit/01d1cb9da10ee013a4a7008933be7b27158d321e))
* **server:** test ([f9c7172](https://github.com/jegor377/mlops-project/commit/f9c7172b729173f87dbb10f61a30b18ca804668f))
* **server:** test ([1c8d685](https://github.com/jegor377/mlops-project/commit/1c8d6850874b5c91aa42e3cffba16cd48bb99ed7))
* **server:** test ([348154e](https://github.com/jegor377/mlops-project/commit/348154e7754960dcffa39458535d53337ee5d539))
* **server:** test commit ([0fee428](https://github.com/jegor377/mlops-project/commit/0fee428139ab119cf62c36e4bbde1ee871861e2a))

## [0.5.0](https://github.com/jegor377/mlops-project/compare/server@v0.4.0...server@v0.5.0) (2026-01-06)


### Features

* **server:** adds get_version endpoint ([28b7523](https://github.com/jegor377/mlops-project/commit/28b7523562232731c786e8c7198739d1650e3984))
* **server:** adds get_version endpoint ([341bbd7](https://github.com/jegor377/mlops-project/commit/341bbd7903aacbcc43c301b4aec2595c807d5b25))

## [0.4.0](https://github.com/jegor377/mlops-project/compare/server@v0.3.0...server@v0.4.0) (2026-01-06)


### Features

* **server:** adds test method ([bdd296f](https://github.com/jegor377/mlops-project/commit/bdd296f77d4159e04521b4d09eeb74fc6645d4c6))
* **server:** adds test method ([8877415](https://github.com/jegor377/mlops-project/commit/8877415fff64a60e20024789bcb2c47acad5b6f5))
* **server:** adds test method ([eb03d87](https://github.com/jegor377/mlops-project/commit/eb03d87fb79199d8eee35455720d4a73bf686edf))
* **server:** remove test method ([80f5390](https://github.com/jegor377/mlops-project/commit/80f53908792626e180c8e196960ed73dec5f747a))
* **server:** remove test method ([27eab6a](https://github.com/jegor377/mlops-project/commit/27eab6a882bc6729878825c20ce820bb7b4c83d1))
* **server:** removes test method ([0c9e2d3](https://github.com/jegor377/mlops-project/commit/0c9e2d3ebfbe88b4db1482387bff5c9ce2a9f61b))
* update uv server lock ([6fb294e](https://github.com/jegor377/mlops-project/commit/6fb294e07b4d58e7df37d09af47c1acb600abfb4))

## [0.3.0](https://github.com/jegor377/mlops-project/compare/server@v0.2.0...server@v0.3.0) (2026-01-06)


### Features

* **server:** remove test method and change release-please config ([1f6b9a6](https://github.com/jegor377/mlops-project/commit/1f6b9a60be6045e016993693c6c13c1a51ee636e))

## [0.2.0](https://github.com/jegor377/mlops-project/compare/server@v0.1.0...server@v0.2.0) (2026-01-06)


### Features

* **server:** adds test method back and changes release-please token ([b1754d8](https://github.com/jegor377/mlops-project/commit/b1754d830da665b0ad86fc5567bcd187359a1de1))
* **server:** remove method test ([41f4666](https://github.com/jegor377/mlops-project/commit/41f4666b7184eb64f79c53a158065f4d739ad4c5))
* **server:** test server change ([566a3fd](https://github.com/jegor377/mlops-project/commit/566a3fde8d13ce6616d559913d194ad1f0e590bd))


### Bug Fixes

* **server:** adjust release-please path mapping ([18e8a6d](https://github.com/jegor377/mlops-project/commit/18e8a6dac20ac75c77695b3fa853e3cfe8d3c8e9))
* **server:** refresh manifest and changelog generation ([65587c9](https://github.com/jegor377/mlops-project/commit/65587c9d6e892b8e35eb072403bfbde2a2fd0eef))
* update release-please config to resolve tree error ([e074721](https://github.com/jegor377/mlops-project/commit/e074721dab6e1eff791a850155e5bf97160207b3))
