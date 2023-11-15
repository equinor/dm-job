# Changelog

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
