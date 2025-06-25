import datetime
import json
import logging
from itemadapter import ItemAdapter

class CorruptionDetectorPipeline:
    def open_spider(self, spider):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.path = f'corruption_data_{timestamp}.json'
        self.first_item = True

    def close_spider(self, spider):
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write('\n]')

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        adapter['date_scraped'] = datetime.datetime.now().astimezone().isoformat()

        line = json.dumps(dict(adapter), ensure_ascii=False)
        with open(self.path, 'a', encoding='utf-8') as f:
            if self.first_item:
                f.write('[\n' + line)
                self.first_item = False
            else:
                f.write(',\n' + line)
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
