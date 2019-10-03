import jinja2, os

from docxtpl import DocxTemplate
from subprocess import Popen

from django.conf import settings


class Generator:
    """
    Class to create Word-documents from templates and incoming data
    """

    def __init__(self, template_dir, template_name, context=None):
        """
        :param template_dir: str
        :param template_name: str
        :param context: context to render to document's template
        """

        self.template_dir = template_dir
        self.template_path = os.path.join(template_dir, template_name + '.docx')
        self.document_path_doc = os.path.join(settings.MEDIA_ROOT, template_name + '.docx')
        self.document_path_pdf = os.path.join(settings.MEDIA_ROOT, template_name + '.pdf')

        self.context = context

        self.jinja_env = jinja2.Environment()
        self.set_jinja_filters()

        self.create()

    def set_jinja_filters(self):
        """
        Extend jinja with template filters
        """
        self.jinja_env.filters['f'] = lambda a: a[:len(a) // 2 if not len(a) % 2 else len(a) // 2 + 1 ]
        self.jinja_env.filters['l'] = lambda a: a[ len(a) // 2 if not len(a) % 2 else len(a) // 2 + 1:]
        self.jinja_env.filters['s'] = lambda a: ', '.join(a)

    def generate_word(self):
        """
        Finally, generate Word-document from template
        """
        doc = DocxTemplate(self.template_path)
        doc.render(self.context, jinja_env=self.jinja_env)
        doc.save(self.document_path_doc)

    def generate_pdf(self):
        """
        Generate PDF-document from Word-document
        """
        Popen([
            settings.LIBREOFFICE_CALL,
            '--headless',
            '--convert-to',
            'pdf',
            self.document_path_doc,
            '--outdir',
            settings.MEDIA_ROOT
            ]).communicate()

    def create(self):
        """
        Generate document after successful validation
        """
        self.generate_word()
        self.generate_pdf()
        return self
