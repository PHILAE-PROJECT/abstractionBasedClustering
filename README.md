# abstractionBasedClustering

Directory abstractionBasedClustering includes a json version of the clustering algorithm based on abstractions.
The same algorithm is used in `../csvTools/ReduceTestSuite.py`.

- *ClusterAgilkiaTestSuite.py* : clusters a json file, storing an agilkia trace_set, based on abstractions of the events.  This tool is a builder.

More documentation is provided in the headers of the python file. 

## Examples

### Clustering an agilkia json trace_set

Script `ClusterAgilkiaTestSuite.py` takes as argument a json file, storing an agilkia trace_set, and an abstraction function. 
It applies the abstraction function to each of the test cases (i.e. Agilkia traces) and clusters the test cases based on their abstraction.

```
ClusterAgilkiaTestSuite.py traces/1026-steps.AgilkiaTraces.json OpNames_Seq_NoSt
```

Using abstraction function `OpNames_Seq_NoSt` produces 11 clusters. The resulting file is stored in

`traces/1026-steps.AgilkiaTraces.Clustered/1026-steps.AgilkiaTraces_OpNames_Seq_NoSt.json`

The following abstraction functions are available (same as for csv files):

```
	OpNames_Set
	OpNamesAndRet_Set
	OpNamesAndAbsRet_Set
	OpNames_Bag
	OpNamesAndRet_Bag
	OpNamesAndAbsRet_Bag
	OpNames_Seq
	OpNamesAndRet_Seq
	OpNamesAndAbsRet_Seq
	OpNames_Seq_NoSt
	OpNamesAndRet_Seq_NoSt
	OpNamesAndAbsRet_Seq_NoSt
```

Use them as the second argument of the ClusterAgilkiaTestSuite script. As for csv files, it is also possible to activate the 
subsumption check, which deletes the clusters that are subsumed by a larger cluster. 
This is activated by an integer in the API or through the GUI. When subsumption is activated, an
appropriate function (subset, subbag, prefix, matchedBy) is selected depending on the initial abstraction function.

 



 


 