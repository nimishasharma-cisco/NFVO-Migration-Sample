# nfvo-migration-sample
Sample package and steps for migrating vnf-info services from NFVO Version 3.7.5-migrate build to NFVO Version 4.2.1 (or newer). 

Assumptions:
1) Users have NSO version compatible with NFVO 4.2.x or later.
2) Users have a NFVO v4.2.x compliant VNFD available. For a comparison of the VNFD structures between Rel 2 and NFVO v4.2.x versions
3) Users have a modified service code that is compliant with the NFVO v4.2.x North Bound API.
4) Users have the Rel 2 packages compiled and loaded into NSO.
5) ESC device has been upgraded to v5.x that is compatible with your NFVO v4.2.x.


Overview of steps for migration

![image](https://wwwin-github.cisco.com/storage/user/89/files/3c07d400-a9a7-11ea-987d-c02def5927bf)
