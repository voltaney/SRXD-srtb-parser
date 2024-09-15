"""独自例外"""


class SrtbError(ValueError):
    """SRTBファイルのパースに失敗した際の例外"""

    pass


class SrtbJsonFormatError(SrtbError):
    """SRTBファイルのデコードに失敗した際の例外"""

    pass


class SrtbKeyError(SrtbError):
    """SRTBファイルに必要なパラメータが存在しない際の例外"""

    pass
