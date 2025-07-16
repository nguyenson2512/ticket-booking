from elasticsearch import Elasticsearch
from core.config import settings

ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL
es_client = Elasticsearch(ELASTICSEARCH_URL)
