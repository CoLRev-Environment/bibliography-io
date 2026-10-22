"""Generic bibliographic field and entry-type names."""


class Fields:
    """Common bibliographic field names used by loaders and writers."""

    ID = "ID"
    ENTRYTYPE = "ENTRYTYPE"

    TITLE = "title"
    AUTHOR = "author"
    EDITOR = "editor"
    YEAR = "year"
    DATE = "date"
    JOURNAL = "journal"
    BOOKTITLE = "booktitle"
    CONTAINER_TITLE = "container_title"
    CHAPTER = "chapter"
    PUBLISHER = "publisher"
    INSTITUTION = "institution"
    SCHOOL = "school"
    ADDRESS = "address"
    VOLUME = "volume"
    NUMBER = "number"
    PAGES = "pages"
    EDITION = "edition"
    MONTH = "month"
    SERIES = "series"
    LANGUAGE = "language"
    DOI = "doi"
    URL = "url"
    ISSN = "issn"
    ISBN = "isbn"
    ABSTRACT = "abstract"
    KEYWORDS = "keywords"

    # Retained because existing tabular writers expose the linked file field.
    FILE = "file"

    # CoLRev metadata is preserved as record payload in BibTeX, not interpreted
    # as generic bibliography semantics.
    ORIGIN = "colrev_origin"
    STATUS = "colrev_status"
    MD_PROV = "colrev_masterdata_provenance"
    D_PROV = "colrev_data_provenance"
    PDF_ID = "colrev_pdf_id"
    SCREENING_CRITERIA = "screening_criteria"
    PRESCREEN_EXCLUSION = "prescreen_exclusion"
    GROBID_VERSION = "grobid-version"
    DBLP_KEY = "colrev.dblp.dblp_key"
    SEMANTIC_SCHOLAR_ID = "colrev.semantic_scholar.id"
    WEB_OF_SCIENCE_ID = "colrev.web_of_science.unique-id"


class ENTRYTYPES:
    """Common, open-vocabulary bibliographic entry types."""

    ARTICLE = "article"
    INPROCEEDINGS = "inproceedings"
    BOOK = "book"
    INBOOK = "inbook"
    PROCEEDINGS = "proceedings"
    INCOLLECTION = "incollection"
    PHDTHESIS = "phdthesis"
    THESIS = "thesis"
    MASTERSTHESIS = "masterthesis"
    BACHELORTHESIS = "bachelorthesis"
    TECHREPORT = "techreport"
    UNPUBLISHED = "unpublished"
    MISC = "misc"
    SOFTWARE = "software"
    ONLINE = "online"
    CONFERENCE = "conference"

    @classmethod
    def get_all(cls) -> list[str]:
        """Return defined common entry types; consumers may accept others."""
        return [
            cls.ARTICLE,
            cls.INPROCEEDINGS,
            cls.BOOK,
            cls.INBOOK,
            cls.PROCEEDINGS,
            cls.INCOLLECTION,
            cls.PHDTHESIS,
            cls.MASTERSTHESIS,
            cls.BACHELORTHESIS,
            cls.TECHREPORT,
            cls.UNPUBLISHED,
            cls.MISC,
            cls.SOFTWARE,
            cls.ONLINE,
            cls.CONFERENCE,
        ]


class Colors:
    """ANSI color sequences used for loader diagnostics."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
