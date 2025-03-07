# Change Log

## [2.0.1] - 2025-03-07
- Added exception handling when performing logout operations with test user accounts to prevent the tool from crashing
- Fixed error messages when verifying boot override settings
- Fixed test account creation to skip verification if the account creation fails
- Corrected tracking of supported boot parameters, which is used to dictate boot override test sequences
- Changed power/reset testing to use 'On' and 'ForceOn' as the final tests to have systems powered on when testing completes

## [2.0.0] - 2025-02-14
- Rewrote the tool to wrap all testing into a single process and produce a singular HTML report

## [1.0.8] - 2021-10-22
- Corrected the '$expand' argument for 'Links' in the query parameter checker
- Added check for the support of '$levels' prior to testing in the query parameter checker

## [1.0.7] - 2021-08-06
- Added manager Ethernet interface checker

## [1.0.6] - 2021-03-02
- Added query parameters checker

## [1.0.5] - 2020-07-06
- Modified all tests to make better use of exception handling for consistent error reporting
- Fixed power control test where the reset type being tested was not being provided to the service
- Made enhancement to the power control test to add more intelligence in the 'PowerState' checking

## [1.0.4] - 2020-05-22
- Added check in one time boot test to verify 'Continuous' is allowed for configuring the boot object
- Enhanced error reporting in one time boot test to make better use of exception handling for reporting test errors

## [1.0.3] - 2020-05-14
- Increased minimum version of redfish_utilities to 1.0.6
- Added a new check in the power/thermal test to verify sensors do not have bogus readings
- Added check in account test to see if the test account is enabled before trying to enable it
- Added fallback attempts in the account test to use different usernames to avoid possible name collision
- Added fallback attempts in the account test to use different passwords in case the service has complexity rules

## [1.0.2] - 2019-11-01
- Made a fix in the one time boot test to check that BootSourceOverrideEnabled is set back to Disabled

## [1.0.1] - 2019-10-11
- Added tracking of system URIs to the power control test to support pre-1.6.0 services
- Added checking for the presence of the PowerState property in the power control test

## [1.0.0] - 2019-07-19
- Updated account management tools to leverage redfish_utilities

## [0.9.5] - 2019-07-12
- Updated one time boot, sensor list, and power control tools to leverage redfish_utilities

## [0.9.2] - 2017-04-27
- Added JSON schema validation
- Added more unit tests

## [0.9.1] - 2017-04-03
- Added new tool to perform account management commands

## [0.9.0] - 2017-03-31
- Initial Release
- Includes a tool to perform power control commands
