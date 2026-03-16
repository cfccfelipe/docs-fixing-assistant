import logging
import re
import string
import unicodedata
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path
from typing import Any

# Seguridad: dET para parsing, defuse_stdlib para asegurar la lib estándar
import defusedxml.ElementTree as dET
from defusedxml import defuse_stdlib

from domain.ports.tool import ITool
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import FileSystemException
from infrastructure.adapters.storage.base_storge import StorageContextMixin

# Asegura que las funciones de parsing de la librería estándar sean seguras
defuse_stdlib()

logger = logging.getLogger(__name__)


class AtomicSourceStorageTool(StorageContextMixin, ITool):
    name = "store_atomic_source"
    description = "Guarda XML atómico con seguridad XXE y metadata del directorio raíz del proyecto."
    parameters = {
        "type": "object",
        "properties": {
            "raw_content": {"type": "string", "description": "Markdown o XML"},
            "file_name": {"type": "string", "description": "Nombre original"},
            "storage_path": {
                "type": "string",
                "description": "Ruta destino (carpeta xml)",
            },
        },
        "required": ["raw_content", "file_name", "storage_path"],
    }

    @handle_errors(
        exception_cls=FileSystemException,
        layer="Infrastructure",
        component="AtomicSourceStorageTool",
        operation="clean_and_store",
    )
    def execute(self, **kwargs: Any) -> str:
        raw_content = kwargs.get("raw_content")
        file_name = kwargs.get("file_name")
        storage_path = kwargs.get("storage_path")

        if not raw_content or not file_name or not storage_path:
            raise ValueError("Faltan parámetros requeridos")

        # Sanitización y resolución de ruta
        safe_file_name = "".join(
            c for c in file_name if c in string.ascii_letters + string.digits + "_-"
        )
        dest_path = Path(storage_path).resolve() / f"{safe_file_name}.xml"
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # OBTENER EL DIRECTORIO PADRE REAL (el que está arriba de /xml)
        # Si dest_path es .../mi-proyecto/xml/archivo.xml -> actual_parent es "mi-proyecto"
        actual_parent = dest_path.parent.parent.name

        is_xml_input = raw_content.strip().startswith("<")
        cleaned_text = (
            raw_content if is_xml_input else self._clean_markdown(raw_content)
        )

        if dest_path.exists():
            xml_output = self._update_existing_xml(dest_path, cleaned_text)
            operation = "updated"
        else:
            xml_output = self._assemble_new_xml(cleaned_text, file_name, actual_parent)
            operation = "created"

        with self.safe_access(str(dest_path), "w", storage_type="local") as f:
            f.write(xml_output)

        logger.info(f"Fuente atómica {operation} exitosamente en {dest_path}")
        return str(dest_path)

    def _update_existing_xml(self, path: Path, new_text: str) -> str:
        """Parsea el archivo existente de forma segura y actualiza el segmento de contenido."""
        # PARSING SEGURO: Usamos defusedxml
        tree = dET.parse(path)
        root = tree.getroot()

        metadata = root.find("metadata")
        if metadata is not None:
            allowed = ["ORIGINAL_FILE_NAME", "PARENT_DIRECTORY"]
            for element in list(metadata):
                if element.tag not in allowed:
                    metadata.remove(element)

            # Asegurar que PARENT_DIRECTORY sea el correcto al actualizar
            parent_tag = metadata.find("PARENT_DIRECTORY")
            if parent_tag is not None:
                parent_tag.text = path.parent.parent.name
            else:
                # CREACIÓN SEGURA: Usamos la lib estándar para crear el nodo
                ET.SubElement(
                    metadata, "PARENT_DIRECTORY"
                ).text = path.parent.parent.name

        segment = root.find("segment[@id='1']")
        if segment is not None:
            segment.clear()
            segment.attrib = {"id": "1"}
            # Si el contenido es XML, lo parseamos antes de inyectarlo
            if new_text.strip().startswith("<"):
                try:
                    segment.append(dET.fromstring(new_text))
                except Exception:
                    segment.text = new_text
            else:
                segment.text = new_text

        return ET.tostring(root, encoding="unicode")

    def _assemble_new_xml(
        self, text: str, original_name: str, parent_folder: str
    ) -> str:
        """Crea una estructura XML nueva desde cero."""
        # CREACIÓN SEGURA: Usamos ET para definir la estructura
        root = ET.Element("root")
        metadata = ET.SubElement(root, "metadata")

        ET.SubElement(metadata, "ORIGINAL_FILE_NAME").text = original_name
        ET.SubElement(metadata, "PARENT_DIRECTORY").text = parent_folder

        segment = ET.SubElement(root, "segment", id="1")

        # PARSING SEGURO: Si el texto inyectado es XML estructurado
        if text.strip().startswith("<"):
            try:
                segment.append(dET.fromstring(text))
            except Exception:
                segment.text = text
        else:
            segment.text = text

        return ET.tostring(root, encoding="unicode")

    def _clean_markdown(self, text: str) -> str:
        """Lógica de limpieza de Markdown para normalizar el contenido."""
        text = re.sub(r"<metadata>[\s\S]*?</metadata>", "", text)
        text = re.sub(r'</?segment id="\d+">', "", text)
        code_blocks = re.findall(r"```[\s\S]*?```", text)
        for i, block in enumerate(code_blocks):
            text = text.replace(block, f"__CODE_BLOCK_{i}__")
        text = re.sub(r"^---[\s\S]*?---", "", text, flags=re.M)
        text = re.sub(r"%%[\s\S]*?%%", "", text)
        text = re.sub(r"```dataview[\s\S]*?```", "", text)
        text = re.sub(r"!\[\[.*?\]\]", "", text)
        text = re.sub(
            r"^(#+)\s+(.*)$",
            lambda m: f" [LEVEL_{len(m.group(1))}] {m.group(2)} ",
            text,
            flags=re.M,
        )
        text = "".join(
            c
            for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )
        text = text.replace("|", " ").replace("[[", "").replace("]]", "")
        text = re.sub(r"\s+", " ", text).strip()
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)
        return text
