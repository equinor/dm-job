# Changelog

## [1.5.1](https://github.com/equinor/dm-job/compare/v1.5.0...v1.5.1) (2024-01-10)


### Bug Fixes

* add optional name to JobHandler ([2f5d997](https://github.com/equinor/dm-job/commit/2f5d9977cc0f92507914d4c355fdc9a34ba3f540))
* raise ApplicationException (no 500's) ([2e17f25](https://github.com/equinor/dm-job/commit/2e17f2505d3b524cc70af367a51ef2cad31f1a2e))

## [1.5.0](https://github.com/equinor/dm-job/compare/v1.4.7...v1.5.0) (2024-01-05)


### Features

* timerange for which recurring job is able to register jobs ([6038426](https://github.com/equinor/dm-job/commit/6038426473ab06ad3a7cbe0744858610ea767f17))


### Bug Fixes

* local container, no raise exceptions causing 500 ([ad8bfb7](https://github.com/equinor/dm-job/commit/ad8bfb70ec9294f4bf84c3c31094625cbe1999d5))
* make jobStatus an enum ([712de4c](https://github.com/equinor/dm-job/commit/712de4c8ab66819882b06463914fb8bb03aab638))


### Build System

* use a data source template and subst envvars ([de383c3](https://github.com/equinor/dm-job/commit/de383c3adcc8a86e62e58eaa057c919b6eb04a52))

## [1.4.7](https://github.com/equinor/dm-job/compare/v1.4.6...v1.4.7) (2023-12-19)


### Bug Fixes

* recurring job pass PAT to new job ([5e66445](https://github.com/equinor/dm-job/commit/5e664459fe852fae3542e0dddffdc65f0dc9a9d7))
* remove stopped attribute from job ([0eced09](https://github.com/equinor/dm-job/commit/0eced09ab2ee4f4ddebe0b9270dee658741e306c))
* required schedule ([11d28c7](https://github.com/equinor/dm-job/commit/11d28c7d49a3c1ed50c99363a9ca0d77589e6772))
* set reccuring job previous runs to required empty list ([39a4a36](https://github.com/equinor/dm-job/commit/39a4a3667826ccaac7eab05f793756585c369c7f))
* typo ([e345d21](https://github.com/equinor/dm-job/commit/e345d219e8dff35e417ad18fde5991fba2a7519b))

## [1.4.6](https://github.com/equinor/dm-job/compare/v1.4.5...v1.4.6) (2023-12-14)


### Bug Fixes

* update job on status change ([09de7ba](https://github.com/equinor/dm-job/commit/09de7ba709583352b951c2c187548f0cc85b91de))

## [1.4.5](https://github.com/equinor/dm-job/compare/v1.4.4...v1.4.5) (2023-12-14)


### Bug Fixes

* radix runner access noneType ([c9b8412](https://github.com/equinor/dm-job/commit/c9b84128c44c42aebb47e9442fecc43cc0fed481))

## [1.4.4](https://github.com/equinor/dm-job/compare/v1.4.3...v1.4.4) (2023-12-11)


### Bug Fixes

* change returned type from remove endpoint to JobStatus ([5afc7cc](https://github.com/equinor/dm-job/commit/5afc7cc86315e3f2bc7cc9254fb438de0cf7dc52))
* job handler radix job name ([f1c9ada](https://github.com/equinor/dm-job/commit/f1c9ada02f9244e6ccc278703c95ba1f298bddc3))

## [1.4.3](https://github.com/equinor/dm-job/compare/v1.4.2...v1.4.3) (2023-12-08)


### Bug Fixes

* bad mergin of job dicts ([b97c299](https://github.com/equinor/dm-job/commit/b97c2993b1172af92bf73899f005587ae93af6bf))
* bump dm-cli ([12eb99c](https://github.com/equinor/dm-job/commit/12eb99c55f99d6f77753b12e30787d9a6e8f988a))
* kill docker container before remove ([1e187f9](https://github.com/equinor/dm-job/commit/1e187f942930c2db47fcbc8c0eb98f834c470910))
* radix job handler returns int on start bug ([4e4be19](https://github.com/equinor/dm-job/commit/4e4be19fdcce3241304b16e5cee2f7296dd8d13e))
* return status from remove job and start job ([7238c23](https://github.com/equinor/dm-job/commit/7238c237d25269fb84714badfe9d129bd946892e))
* use UUID in the API ([209acaa](https://github.com/equinor/dm-job/commit/209acaa63733eb1efddfc5dce946ef6127c4ec08))

## [1.4.2](https://github.com/equinor/dm-job/compare/v1.4.1...v1.4.2) (2023-11-27)


### Bug Fixes

* add job api url to config ([d144724](https://github.com/equinor/dm-job/commit/d14472403ab4974b13c374510675595646cba655))

## [1.4.1](https://github.com/equinor/dm-job/compare/v1.4.0...v1.4.1) (2023-11-27)


### Bug Fixes

* typo in string split in radix handler ([f09d417](https://github.com/equinor/dm-job/commit/f09d417eabf55191f19cb6696f77c1b65ff40514))

## [1.4.0](https://github.com/equinor/dm-job/compare/v1.3.5...v1.4.0) (2023-11-24)


### Features

* update job progress endpoint ([de05191](https://github.com/equinor/dm-job/commit/de051910dea8c99633813e79df150f014a80eeca))


### Bug Fixes

* add back not started ([51e7fe0](https://github.com/equinor/dm-job/commit/51e7fe02f84d5ac65bc7f05d0631600690d124a1))
* adjust when job status is set and save status removed to dmss ([a075441](https://github.com/equinor/dm-job/commit/a07544105003364eeae2a0f9fab4f0a1923a73ce))
* append log fromat ([da4a8a0](https://github.com/equinor/dm-job/commit/da4a8a01bfc0936b76976bc405aa7531c84d2355))
* append log to existing job log if status changed ([891e1ff](https://github.com/equinor/dm-job/commit/891e1ff9c368fb3c287843d9c8c7921c8e7c2cd7))
* force log flag in update progress ([09a692a](https://github.com/equinor/dm-job/commit/09a692a9aceb30f2911ce315dfbf5f47c439ccf3))
* make job handler progress return additional message ([0c7bdb4](https://github.com/equinor/dm-job/commit/0c7bdb4bd96a7700af270c0bed2421d973e4b114))
* Make the api return the entire radix response when radix job handler progress is invoked ([fe880ec](https://github.com/equinor/dm-job/commit/fe880ecb5669433a87c6081ba778b69defa47b07))
* remove job even if handler not implement method ([fff568f](https://github.com/equinor/dm-job/commit/fff568f65fafd14a4a4f8e7ba0db79af82891331))
* update all job hanlder progress methods to include message ([533e7c2](https://github.com/equinor/dm-job/commit/533e7c243d2e1cedbe111d6e8ed828d9abac4380))
* use append logs if status has changed in job_progress endpoint ([3139cd6](https://github.com/equinor/dm-job/commit/3139cd61985a7dfd5e3e9a31877c2824453368b8))

## [1.3.5](https://github.com/equinor/dm-job/compare/v1.3.4...v1.3.5) (2023-11-17)


### Bug Fixes

* add separate blueprint for local container runner ([1288afb](https://github.com/equinor/dm-job/commit/1288afba23573e58a027b4eaa992fbe4e2a54c0c))

## [1.3.4](https://github.com/equinor/dm-job/compare/v1.3.3...v1.3.4) (2023-11-16)


### Bug Fixes

* add local docker network name to container runner ([bd3b645](https://github.com/equinor/dm-job/commit/bd3b645a497037d9148fc7048949dd1e66500274))
* make environment varaibles optional for local container runner ([432288b](https://github.com/equinor/dm-job/commit/432288ba68d32b950713eb5534551f346238f90d))

## [1.3.3](https://github.com/equinor/dm-job/compare/v1.3.2...v1.3.3) (2023-11-16)


### Bug Fixes

* remove abstract from job blueprint ([e3fef28](https://github.com/equinor/dm-job/commit/e3fef280259b74af46c6859903680125c2e31cbc))

## [1.3.2](https://github.com/equinor/dm-job/compare/v1.3.1...v1.3.2) (2023-11-15)


### Bug Fixes

* check to handle if job_status is called before start has completed ([b6d436e](https://github.com/equinor/dm-job/commit/b6d436ee49cbb002723d5e707a924e7645584b5a))


### Code Refactoring

* make Local containers use runner name ([efbbe99](https://github.com/equinor/dm-job/commit/efbbe9926499a365d379c6fddd664e001348e9a6))
* use pydantic model for job class ([2752aa5](https://github.com/equinor/dm-job/commit/2752aa558872a200562b6eb0f9b472722a7ca574))

## [1.3.1](https://github.com/equinor/dm-job/compare/v1.3.0...v1.3.1) (2023-11-10)


### Bug Fixes

* implement environmentVariables from job runner entity in rtadix job handler ([e21c814](https://github.com/equinor/dm-job/commit/e21c8142bf28fdec72bbea1aeaa7b3794837d94c))
* move dmss variables into environment variables in runner entity ([2086db0](https://github.com/equinor/dm-job/commit/2086db09f99f61b3b90312b7f470f698addab981))


### Code Refactoring

* simplify list_of_env_to_dict function ([6ba4de9](https://github.com/equinor/dm-job/commit/6ba4de976b9dcefb99836f29d68d74cab924572e))

## [1.3.0](https://github.com/equinor/dm-job/compare/v1.2.4...v1.3.0) (2023-11-09)


### Features

* RecurringJobHandler ([39da290](https://github.com/equinor/dm-job/commit/39da2905aa864c64268182d38fbee24a8a96dc91))

## [1.2.4](https://github.com/equinor/dm-job/compare/v1.2.3...v1.2.4) (2023-10-24)


### Bug Fixes

* cron job support ([1ac7d1a](https://github.com/equinor/dm-job/commit/1ac7d1a6b9eac66852ff1db5d74f98b927c7bc54))
* default name for job docker container ([b4d1cbd](https://github.com/equinor/dm-job/commit/b4d1cbde3e5e3747a4ad1661e8fb30dc2c33927b))
* deterministic default name for local container ([11ef33f](https://github.com/equinor/dm-job/commit/11ef33f6b48eee27ada46d9269ae6e0026d69476))
* remove singleton ([edaecc5](https://github.com/equinor/dm-job/commit/edaecc5bb9d2fc6e659d96da71005dc4bb85f6cb))
* small fix ([4e00d41](https://github.com/equinor/dm-job/commit/4e00d413dd54e6afe2a689114f90cfd7bfc75544))
* turn job service into singleton ([b50f42d](https://github.com/equinor/dm-job/commit/b50f42d0845e5662249e0083d763e1b79979cad1))

## [1.2.3](https://github.com/equinor/dm-job/compare/v1.2.2...v1.2.3) (2023-10-19)


### Bug Fixes

* allow local container jobs to run local images ([0319946](https://github.com/equinor/dm-job/commit/0319946004d479546afda7a25c403c2c7a746d13))
* **mypy:** failing CI from mypy error ([4df66f8](https://github.com/equinor/dm-job/commit/4df66f81091dc1be5445daa91fdea61e7abd1d7d))

## [1.2.2](https://github.com/equinor/dm-job/compare/v1.2.1...v1.2.2) (2023-10-11)


### Bug Fixes

* include job dmss_id in in job payload ([36a430f](https://github.com/equinor/dm-job/commit/36a430f0a63cac71809c3c103639427bdf918f03))
* make radix job handler return status code instead of calling status ([48b9ae2](https://github.com/equinor/dm-job/commit/48b9ae22e50b06377047fdd29f68f658aead4162))
* permission deined results folder ([706b959](https://github.com/equinor/dm-job/commit/706b959d66646a8da5325f16b45f5a89924089bb))


### Code Refactoring

* remove print data source ([b7b813e](https://github.com/equinor/dm-job/commit/b7b813e24e57004faf90f5755ccfadbe0de46b11))

## [1.2.1](https://github.com/equinor/dm-job/compare/v1.2.0...v1.2.1) (2023-09-26)


### Bug Fixes

* set data source from environment variable ([08fe04f](https://github.com/equinor/dm-job/commit/08fe04f72b3318b28275012b197c90590ed7f64a))

## [1.2.0](https://github.com/equinor/dm-job/compare/v1.1.0...v1.2.0) (2023-09-25)


### Features

* add data source from environment ([8ef5ded](https://github.com/equinor/dm-job/commit/8ef5dedfeaedaa9362cad6367dcc394b0bedc213))

## [1.1.0](https://github.com/equinor/dm-job/compare/v1.0.7...v1.1.0) (2023-09-15)


### Features

* add radix job handler ([c72fec7](https://github.com/equinor/dm-job/commit/c72fec78bc9edcd461b22be2bcb24e4f4d0844c6))


### Code Refactoring

* add oauth scope to swagger ([92ef6b0](https://github.com/equinor/dm-job/commit/92ef6b0d7258f611ed261abf0dd32366c45a3dd6))


### Build System

* correct command to start application ([5875e2b](https://github.com/equinor/dm-job/commit/5875e2bac8f364beab7d69030008965f0d31df2d))

## [1.0.7](https://github.com/equinor/dm-job/compare/v1.0.6...v1.0.7) (2023-09-05)


### Bug Fixes

* adjust depth parameter ([61b8fc7](https://github.com/equinor/dm-job/commit/61b8fc7c9e024e875d2be6a30fc153db649023e8))


### Build System

* stop using venv inside docker ([135c91c](https://github.com/equinor/dm-job/commit/135c91c44ce87704202e53fe19d3140dfeea2f58))


### Continuous Integration

* lock dmss version ([752e3a0](https://github.com/equinor/dm-job/commit/752e3a0a4499f6c9a11cbc3da45d4c3a1e6f5a9e))

## [1.0.6](https://github.com/equinor/dm-job/compare/v1.0.5...v1.0.6) (2023-08-29)


### Bug Fixes

* bug in split_address() ([b537ebf](https://github.com/equinor/dm-job/commit/b537ebf6bc880d64689a73a9b4ad000060f4f6dc))
* fix publish yaml error ([4534051](https://github.com/equinor/dm-job/commit/4534051e7550a660e3423e2e0f02f5ebadd6a117))
* inside status_job(), check if results exist in job_entity before accessing this attribute ([c391292](https://github.com/equinor/dm-job/commit/c3912924b15e79cc180bc6c0380a90ea1fe253db))
* test for reverse description ([9c70a27](https://github.com/equinor/dm-job/commit/9c70a27d48e55af12c6d4e9bef8542f761e21433))


### Documentation

* add docstrings to functions in job_service.py ([1847040](https://github.com/equinor/dm-job/commit/1847040c2ec80b9f27bbccec941bc0b0df0b374c))
* add more documentation to job API endpoints ([2eef466](https://github.com/equinor/dm-job/commit/2eef466914a78a0d8b78a7a3a0a148239518d3a1))
* update docstring of _get_job_handler ([41855b0](https://github.com/equinor/dm-job/commit/41855b00c4871753e7345243a02af8630b243dfe))


### Styles

* fix bandit errors ([ab53a3d](https://github.com/equinor/dm-job/commit/ab53a3ddc8dd7a331f6a82f62d55b8996a0c11b3))
* fix black errors ([998100e](https://github.com/equinor/dm-job/commit/998100e568f8e20197cd94e8790846b2551a1a1a))
* fix mypy errors ([45224bf](https://github.com/equinor/dm-job/commit/45224bf3c18069ca8837782c2d02dac38704f90e))
* fix pretty-format-json errors ([c93d039](https://github.com/equinor/dm-job/commit/c93d039875cd58e01e14fdf00894b10ebee1ef76))


### Miscellaneous Chores

* **pre-commit:** add and update hooks ([f1349d9](https://github.com/equinor/dm-job/commit/f1349d9f722aeed895a3c65b99d501e417b0b147))
* update codeowners ([9b8cfdf](https://github.com/equinor/dm-job/commit/9b8cfdf1ce7aca3d4d2a7c64a1c1c53312e5d21f))
* update pre-commit version ([9897512](https://github.com/equinor/dm-job/commit/9897512b47f72f6daf3a40649d9f526c05a38ea1))


### Continuous Integration

* add release-please ([6a7628f](https://github.com/equinor/dm-job/commit/6a7628f782007317f02e7c18c2107f61cd67ab2e))
* avoid running no-commit-to-branch on PR merge ([a519bf1](https://github.com/equinor/dm-job/commit/a519bf1fbbe5aaeb411748ba9b4f85a383938188))
