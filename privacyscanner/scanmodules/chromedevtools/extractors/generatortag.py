import pychrome

from privacyscanner.scanmodules.chromedevtools.extractors.base import Extractor
from privacyscanner.scanmodules.chromedevtools.utils import scripts_disabled


ELEMENT_NODE = 1


class GeneratorTagExtractor(Extractor):

    GENERATOR_KEYWORDS = ['generator', 'Generator']

    def extract_information(self):
        # Disable scripts to avoid DOM changes while searching for generator tags
        with scripts_disabled(self.page.tab, self.options):
            self._extract_information()

    def extract_information(self):
        tags = []

        node_id = self.page.tab.DOM.getDocument()['root']['nodeId']
        meta_node_ids = self.page.tab.DOM.querySelectorAll(nodeId=node_id, selector='meta')['nodeIds']

        for node_id in meta_node_ids:
            while node_id is not None:
                try:
                    node = self.page.tab.DOM.describeNode(nodeId=node_id)['node']
                except pychrome.CallMethodException:
                    # For some reason, nodes seem to disappear in-between,
                    # so just ignore these cases.
                    break
                if node['nodeType'] == ELEMENT_NODE and node['nodeName'].lower() == 'meta':
                    if node['attributes'][1] == 'generator':
                        tags.append(node['attributes'][3])
                        break
                node_id = node.get('parentId')

        tags = list(set(tags))
        generator_tags = []
        if tags:
            for element in tags:
                generator_tags.append(element)
            self.result['generator'] = generator_tags
        else:
            self.result['generator'] = None
