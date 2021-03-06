# nfvo-migration-sample
Sample package and steps for migrating vnf-info services from NFVO Version 3.7.5-migrate build to NFVO Version 4.2.1 (or newer). 

### Assumptions:
<ol>
<li>Users have NSO version compatible with NFVO 4.2.x or later.</li>
<li>Users have a NFVO v4.2.x compliant VNFD available. For a comparison of the VNFD structures between Rel 2 and NFVO v4.2.x versions.</li>
<li>Users have a modified service code that is compliant with the NFVO v4.2.x North Bound API.</li>
<li>Users have the Rel 2 packages compiled and loaded into NSO.</li>
<li>ESC device has been upgraded to v5.x that is compatible with your NFVO v4.2.x.</li>
</ol>


### Overview of steps for migration

![image](https://user-images.githubusercontent.com/66647064/84090999-1b8c4980-a9a8-11ea-8b45-2fde6e3bbb76.png)

### Detail Documentation

Detailed steps for migration can be found [here](https://github.com/nimishasharma-cisco/NFVO-Migration-Sample/blob/master/docs/NFVO%20Migration%20Document.pdf)
