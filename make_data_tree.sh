#!/usr/bin/env bash


# Tree Configuration
DATA_ROOT=data

GENES=${DATA_ROOT}/genes
GENES_RAW=${GENES}/raw

F5_TSS=${DATA_ROOT}/tss/fantom5

F5_ENH=${DATA_ROOT}/enhancers/fantom5
F5_ENH_RAW=${F5_ENH}/raw

ENC_ENH=${DATA_ROOT}/enhancers/encode
ENC_ENH_RAW=${ENC_ENH}/raw

CHROMATIN=${DATA_ROOT}/chromatin
CHROMATIN_RAW=${CHROMATIN}/raw


# Make tree
printf "Making directories tree under %s\n" ${DATA_ROOT}
mkdir -p ${GENES} -v
mkdir -p ${GENES_RAW} -v
mkdir -p ${F5_ENH} -v
mkdir -p ${F5_ENH_RAW} -v
mkdir -p ${f5_TSS} -v
mkdir -p ${ENC_ENH} -v
mkdir -p ${ENC_ENH_RAW} -v
mkdir -p ${CHROMATIN} -v
mkdir -p ${CHROMATIN_RAW} -v


# Create genes.db
printf "Creating genes db\n"
PREDEFINED_GENES_DB_SOURCES=predefined_genes_db_sources
cp ${PREDEFINED_GENES_DB_SOURCES}/*.tsv ${GENES_RAW}/
python3 ${PREDEFINED_GENES_DB_SOURCES}/create_genes_db.py -i ${GENES_RAW} -o ${GENES}/genes.db

# Download FANTOM5 CAGE expression matrix and ontology (to find transcription start sites)
PREDEFINED_F5_TSS_SOURCES=predefined_fantom5_tss_data_sources
printf "Acquiring transcription start sites FANTOM5 data\n"
wget -O ${PREDEFINED_F5_TSS_SOURCES}/hg19.cage_peak_phase1and2combined_tpm.osc.txt.gz 'http://fantom.gsc.riken.jp/5/datafiles/latest/extra/CAGE_peaks/hg19.cage_peak_phase1and2combined_tpm.osc.txt.gz'
wget -O ${PREDEFINED_F5_TSS_SOURCES}/ff-phase2-170801.obo.txt http://fantom.gsc.riken.jp/5/datafiles/latest/extra/Ontology/ff-phase2-170801.obo.txt
# aggregate samples by organs, tissues and cell-types and store location of TSSs in BED files
python ${PREDEFINED_F5_TSS_SOURCES}/aggregate_CAGE_peaks.py ${PREDEFINED_F5_TSS_SOURCES}/ff-phase2-170801.obo.txt ${PREDEFINED_F5_TSS_SOURCES}/hg19.cage_peak_phase1and2combined_tpm.osc.txt.gz ${F5_TSS}
#
# not-tissue-specific TSSs, replaced by the data generated above
#wget -O ${F5_TSS}/promoter_data.bed 'http://promoter.binf.ku.dk/viewer.php?match=and&sort-by=donotsort&end-site=249250621&start-site=1&chr-number=ALL&toggle=basic&return=download'



# Download enhancers fantom5
printf "Acquiring enhancers fantom5 data\n"
wget http://enhancer.binf.ku.dk/presets/facet_expressed_enhancers.tgz -P ${F5_ENH_RAW}
printf "... extracting celltype data"
tar -xzf ${F5_ENH_RAW}/facet_expressed_enhancers.tgz -C ${F5_ENH} --wildcards CL:*
printf "... extracting organ data"
tar -xzf ${F5_ENH_RAW}/facet_expressed_enhancers.tgz -C ${F5_ENH} --wildcards UBERON*


# Download ENCODE enhancers data (ChIP-seq)
PREDEFINED_ENC_ENH_SOURCES=predefined_encode_enhancer_data_sources
printf "Acquiring ENCODE enhancers data\n"
# download raw BED files
awk -F '\t' '$43 ~ hg19 {print $42}' ${PREDEFINED_ENC_ENH_SOURCES}/ENCODE_enhancers_ChipSeq.metadata.tsv | wget -i - -P ${ENC_ENH_RAW}
# generate collapsing script & run it
python3 ${PREDEFINED_ENC_ENH_SOURCES}/collapse_tissue_beds.py ${PREDEFINED_ENC_ENH_SOURCES}/ENCODE_enhancers_ChipSeq.metadata.tsv ${ENC_ENH} ${ENC_ENH} > ${ENC_ENH}/collapse_hg19.sh
chmod u+x ${ENC_ENH}/collapse_hg19.sh && ${ENC_ENH}/collapse_hg19.sh
# delete raw BEDs to save space
# rm -r ${ENC_ENH}


# Download ENCODE accessible chromatin data
PREDEFINED_DNASEQ_SOURCES=predefined_dnaseq_data_sources
printf "Acquiring ENCODE accessible chromatin data\n"
# download raw BED files
awk -F '\t' '$43 ~ hg19 {print $42}' ${PREDEFINED_DNASEQ_SOURCES}/ENCODE_DNase_seq.metadata.tsv | wget -i - -P ${CHROMATIN_RAW}
# generate collapsing script & run it

python3 ${PREDEFINED_DNASEQ_SOURCES}/collapse_tissue_beds.py ${PREDEFINED_DNASEQ_SOURCES}/ENCODE_DNase_seq.metadata.tsv ${CHROMATIN_RAW} ${CHROMATIN}> ${CHROMATIN}/collapse_hg19.sh
chmod u+x ${CHROMATIN}/collapse_hg19.sh && ${CHROMATIN}/collapse_hg19.sh
# delete raw BEDs to save space
# rm -r ${CHROMATIN_RAW}





