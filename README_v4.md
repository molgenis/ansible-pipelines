### Introduction of the bucket system. 
The _analysis_ (for NGS_DNA) and _pipeline_ (GAP pipeline) columns in the samplesheet determine which pipelines will be run. Running multiple pipelines can be selected by a `+` sign (i.e. 
`NGS_Demultiplexing+NGS_DNA`)

- bucket system for pipelines(on tmp0X) 
      - folders: _tmp_, _Samplesheets_, _projects_ and _runs_ have an additional subfolder with the pipeline name i.e. `projects/NGS_DNA/ProjectXX` and `tmp/GAP/GSA_v3-XXX`
      - _logs_ folder and _prm_ remains the same as before
- new script; `moveAndCheckSamplesheets.sh` (originated from MoveSamplesheets):
- `-d` dat_dir, to overwrite the server.cfg/sharedConfig variable: `DAT_ROOT_DIR`  
   - parsing the samplesheet to see what the first step of the pipeline is (and send it to the correct bucket/samplesheetsfolder)*
\* **the value in the samplesheet is now hardcoded until the Darwin team make this variable (e.g. for the NGS_DNA pipeline it is by default `NGS_Demultiplexing+NGS_DNA`**
- new script; `splitAndMoveSamplesheetPerProject.sh`, that handles the splitting of the samplesheet into projects and moving (if required) from NGS_Demultiplexing to NGS_DNA Samplesheets folder
- new script; `copyRawDataToTmp.sh`, that will run on the chaperone machines (where the prm storage is mounted) that handles the copying of the rawdata to tmp (since the introduction of the new diagnostic 
clusters it is no longer possible to pull data). 
This step is required when the rawdata is no longer available on the diagnostic cluster
    - the script will scan the logs directory of tmp0X on the diagnostic clusters and search for `${project}.data.requested files`. These files are created by the NGS_DNA/GAP pipeline and are already in the 
correct format to be used directly by the `rsync` command. 

- Dragen pipeline is also part of the NGS_Automated
     - Merged `PullRawDataFromDS.sh` and `processGsRawData.sh` into one file: `PullAndProcessGsRawData.sh`
           - the raw data from Genomescan is now one directory level deeper (e.g. `${gsBatch}/Raw_data/123.fastq.gz` instead of in `104832-062/123.fastq.gz`) 
     - Created new file for pulling and processing Dragen data: `PullAndProcessGsAnalysisData.sh`
           - analysis data (such as bams, gvcf and vcf files) are in the `${gsBatch}/Analysis`/ folder, per Sample there is one folder. (e.g. `104832-062/Analysis/sample1/sample1.gvcf.gz`)
           - The script will merge all the A,B,C etc samplesheets (e.g. GS_118A, GS_118B) in one samplesheet without the suffix (e.g. GS_118.csv)
     - new script that runs the Dragen pipeline: `startDragenPipeline.sh`
           - it is executed in the umcg-genomescan group or in its test group (umcg-gst)
           - it will execute the NGS_DNA pipeline with the `workflow_DRAGEN.csv` workflow (also part of the NGS_DNA)
- `copyProjectDataToPrm.sh` has extra arguments
     - `-d` dat_dir, to overwrite the server.cfg/sharedConfig variable: `DAT_ROOT_DIR` 
     - `-p` in which samplesheets folder (which pipeline) should the script search (e.g. NGS_DNA, GAP)
     - rawdata will be processed on the same machine as where the NGS_DNA and GAP pipeline run, build in a check if the rawdata has been copied to prm yet, project data will not be copied until.
- `copyRawDataToPrm.sh` has extra arguments:
     - `-p` in which samplesheets folder (which pipeline) should the script search (e.g. NGS_Demultiplexing, DRAGEN, AGCT)
     - `-f`, this argument can be used when the user that executes the script is pulling rawdata not from the inhouse demultiplexing and it comes from a different group. (in case of genomescan/dragen the 
option looks like this: `-f run01.processGsRawData.finished`). This will overwrite the RAWDATAPROCESSINGFINISHED parameter in the group.csv file. This argument will also set a `mergedSamplesheet` variable to 
true. (see below for more info about the mergedSamplesheet)
     -  if the data is copied there will be a message to the diagnostic cluster that the rawdata is finished (this is needed as explained above in the copyProjectDataToPrm part)
          - for regular inhouse data it will create per project in the logsfolder on the diagnostic cluster: run01.rawDataCopiedToPrm.finished
          - in case of genomescan/dragen, the `mergedSamplesheet` variable is true, then the run01.rawDataCopiedToPrm.finished will only be created in the merged projectfolder name (e.g. GS_118)
