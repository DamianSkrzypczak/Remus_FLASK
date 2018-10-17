import os
import re
import logging
from collections import defaultdict

from remus.bio.bed.beds_loading import BedLoader


DATA_DIRECTORIES_MAP = {
    "enhancers/encode": "ENH_EN",
    "enhancers/fantom5": "ENH_F5",
    "chromatin": "CHRM",
    "tss/fantom5": "TSS_F5"
}


class RegulatoryRegionsFilesRegistry:
    
    def __init__(self, root="data",
                 directories_and_symbols=DATA_DIRECTORIES_MAP,
                 extensions=(".bed", ".bed.gz")):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        sources_map = self._make_sources_map(directories_and_symbols, extensions, root)
        
        self._available_tissues = self._create_available_tissues_map(sources_map)
        

    def _make_sources_map(self, directories_and_symbols, extensions, root):
        
        self.logger.info("Making sources map for root: %s ; paths: %s ; and extensions: %s" \
                            % (root, str(directories_and_symbols), str(extensions)))
        
        sources = defaultdict(dict)
        for path in directories_and_symbols:
            for bed in os.listdir(os.path.join(root, path)):
                ontology_and_name = re.match(r"(\w+:\d+)_([^.]+)", bed)
                if ontology_and_name and any([bed.endswith(ext) for ext in extensions]):
                    ontology = ontology_and_name.group(1)
                    name = ontology_and_name.group(2)
                    symbol = directories_and_symbols[path]
                    sources[ontology][symbol] = os.path.join(root, path, bed)
                    sources[ontology]["name"] = name.replace("_expressed_enhancers", "").replace("_promoters", "").replace("_", " ")
        
        self.logger.debug("Sources map:\n%s" % str(sources))
        
        return sources

    def _create_available_tissues_map(self, sources_map):
        tissues_map = {}
        for onto_num, files_data in sources_map.items():
            source_name = files_data.pop("name")
            name = "{} ({})".format(source_name, ", ".join(sorted(files_data.keys())))
            tissues_map[name] = files_data
        
        self.logger.debug("Tissues map:\n%s" % str(tissues_map))
        return tissues_map


    @property
    def available_tissues(self):
        self.logger.debug("Available tissues:\n%s" % str(self._available_tissues.keys()))
        return list(self._available_tissues.keys())


    def get_bed(self, tissue, source_symbol):
        self.logger.info('Requested tissue [%s] from source [%s]' % (tissue, source_symbol))
        
        if tissue not in self._available_tissues:
            raise InvalidTissueNameException("Querried tissue [%s] was not among available tissue keys:\n%s" % 
                    (tissue, str(self._available_tissues.keys())))
        
        try:
            tissue_path = self._available_tissues[tissue][source_symbol]
            self.logger.info('Found %s' % tissue_path)
            return BedLoader(tissue_path).bed
        except KeyError:
            self.logger.info('No tissue [%s] in source [%s]' % (tissue, source_symbol))
            return None
                

    def get_matching_tissues(self, pattern, limit):
        limit = limit if limit else -1
        pattern = pattern if pattern else " "
        try:
            pattern = re.sub("\s+", ".*", pattern, re.IGNORECASE)
            return sorted([i for i in self.available_tissues if re.search(pattern, i, re.IGNORECASE)])[:limit]
        except LookupError:
            return []


class InvalidTissueNameException(Exception):
    pass
