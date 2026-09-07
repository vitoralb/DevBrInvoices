import logging
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

logger = logging.getLogger(__name__)


def to_xml(obj):
    """Serialize xsdata dataclass object to XML string."""
    try:
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        return serializer.render(obj)
    except Exception as e:
        logger.error("Error serializing object %s to XML: %s", type(obj), e)
        raise
