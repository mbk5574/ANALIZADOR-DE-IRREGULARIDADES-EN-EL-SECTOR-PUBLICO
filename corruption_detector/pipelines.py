import datetime
import json
import logging
from itemadapter import ItemAdapter

class CorruptionDetectorPipeline:
    def open_spider(self, spider):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.file = open(f'corruption_data_{timestamp}.json', 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True  # Indicador del primer item para controlar comas

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False)
        if self.first_item:
            self.file.write(line)
            self.first_item = False
        else:
            self.file.write(",\n" + line)
        return item

class TextCleanerPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get('content_preview'):
            adapter['content_preview'] = adapter['content_preview'].strip()
        if adapter.get('title'):
            adapter['title'] = adapter['title'].replace('\n', ' ').strip()
        
        logging.debug(f"Ítem limpiado: {adapter.get('title', 'Sin título')}")
        return item
