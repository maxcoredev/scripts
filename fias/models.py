# Update FIAS - https://fias.nalog.ru/Updates.aspx

from django.db import models

# Global: used by Object and Stead

class OperationStatus(models.Model):
    """
    Статус действия

    operstatid - Идентификатор статуса (ключ)
    name - Наименование
        01 – Инициация;
        10 – Добавление;
        20 – Изменение;
        21 – Групповое изменение;
        30 – Удаление;
        31 - Удаление вследствие удаления вышестоящего объекта;
        40 – Присоединение адресного объекта (слияние);
        41 – Переподчинение вследствие слияния вышестоящего объекта;
        42 - Прекращение существования вследствие присоединения к другому адресному объекту;
        43 - Создание нового адресного объекта в результате слияния адресных объектов;
        50 – Переподчинение;
        51 – Переподчинение вследствие переподчинения вышестоящего объекта;
        60 – Прекращение существования вследствие дробления;
        61 – Создание нового адресного объекта в результате дробления;
        70 – Восстановление объекта прекратившего существование
    """

    operstatid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'fias\".\"operstat'


# NormativeDocument

class NormativeDocumentType(models.Model):
    """
    Тип нормативного документа

    ndtypeid - Идентификатор записи (ключ)
    name - Наименование типа нормативного документа
    """

    ndtypeid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'fias\".\"ndoctype'


class NormativeDocument(models.Model):
    """
    Сведения по нормативному документу, являющемуся основанием присвоения адресному элементу наименования

    normdocid - Идентификатор нормативного документа
    docname - Наименование документа
    docdate - Наименование документа
    docnum - Номер документа
    doctype - Тип документа
    docimgid - Идентификатор образа (внешний ключ)

    """

    normdocid = models.UUIDField(primary_key=True)
    docname = models.TextField(null=True)
    docdate = models.DateField(null=True)
    docnum = models.CharField(null=True, max_length=20)
    doctype = models.ForeignKey(NormativeDocumentType, on_delete=models.PROTECT)  # PositiveIntegerField()
    docimgid = models.UUIDField(null=True)  # TODO: Куда должен вести этот "внешний ключ"?

    class Meta:
        db_table = 'fias\".\"normdoc'


# Object

class ActualStatus(models.Model):
    """
    Статус актуальности ФИАС

    actstatid - Идентификатор статуса (ключ)
    name - Наименование
        0 – Не актуальный
        1 – Актуальный (последняя запись по адресному объекту)
    """

    actstatid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'fias\".\"actstat'


class AddressObjectType(models.Model):
    """
    Тип адресного объекта

    По всей видимости таблица самостоятельная, и Object на ней не завязан
    Object-у интересен только level в поле aolevel

    level - Уровень адресного объекта
    scname - Краткое наименование типа объекта
    socrname - Полное наименование типа объекта
    kod_t_st - Ключевое поле
    """

    level = models.PositiveIntegerField()
    scname = models.CharField(null=True, max_length=10)
    socrname = models.CharField(max_length=50)
    kod_t_st = models.CharField(max_length=4, primary_key=True)

    class Meta:
        db_table = 'fias\".\"socrbase'
        indexes = [
            models.Index(fields=['scname', 'level'], name='scname_level_idx'),
        ]


class CenterStatus(models.Model):
    """
    Статус центра

    centerstid - Идентификатор статуса
    name - Наименование
    """

    centerstid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'fias\".\"centerst'


class CurrentStatus(models.Model):
    """
    Статус актуальности КЛАДР 4.0

    curentstid - Идентификатор статуса (ключ)
    name - Наименование (0 - актуальный, 1-50, 2-98 – исторический (кроме 51), 51 - переподчиненный, 99 - несуществующий)
    """

    curentstid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'fias\".\"curentst'


class Object(models.Model):
    """
    Классификатор адресообразующих элементов

    aoguid - Глобальный уникальный идентификатор адресного объекта
    formalname - Формализованное наименование
    regioncode - Код региона
    autocode - Код автономии
    areacode - Код района
    citycode - Код города
    ctarcode - Код внутригородского района
    placecode - Код населенного пункта
    plancode - Код элемента планировочной структуры
    streetcode - Код улицы
    extrcode - Код дополнительного адресообразующего элемента
    sextcode - Код подчиненного дополнительного адресообразующего элемента
    offname - Официальное наименование
    postalcode - Почтовый индекс
    ifnsfl - Код ИФНС ФЛ
    terrifnsfl - Код территориального участка ИФНС ФЛ
    ifnsul - Код ИФНС ЮЛ
    terrifnsul - Код территориального участка ИФНС ЮЛ
    okato - OKATO
    oktmo - OKTMO
    updatedate - Дата  внесения записи
    shortname - Краткое наименование типа объекта
    aolevel - Уровень адресного объекта
    parentguid - Идентификатор объекта родительского объекта
    aoid - Уникальный идентификатор записи. Ключевое поле.
    previd - Идентификатор записи связывания с предыдушей исторической записью
    nextid - Идентификатор записи  связывания с последующей исторической записью
    code - Код адресного объекта одной строкой с признаком актуальности из КЛАДР 4.0.
    plaincode - Код адресного объекта из КЛАДР 4.0 одной строкой без признака актуальности (последних двух цифр)
    actstatus - Статус актуальности адресного объекта ФИАС. Актуальный адрес на текущую дату. Обычно последняя запись об адресном объекте.
        0 – Не актуальный
        1 - Актуальный
    centstatus - Статус центра
    operstatus - Статус действия над записью – причина появления записи (см. описание таблицы OperationStatus):
        01 – Инициация;
        10 – Добавление;
        20 – Изменение;
        21 – Групповое изменение;
        30 – Удаление;
        31 - Удаление вследствие удаления вышестоящего объекта;
        40 – Присоединение адресного объекта (слияние);
        41 – Переподчинение вследствие слияния вышестоящего объекта;
        42 - Прекращение существования вследствие присоединения к другому адресному объекту;
        43 - Создание нового адресного объекта в результате слияния адресных объектов;
        50 – Переподчинение;
        51 – Переподчинение вследствие переподчинения вышестоящего объекта;
        60 – Прекращение существования вследствие дробления;
        61 – Создание нового адресного объекта в результате дробления
    currstatus - Статус актуальности КЛАДР 4 (последние две цифры в коде)
    startdate - Начало действия записи
    enddate - Окончание действия записи
    normdocid - UUID нормативного документа
    normdoc - Внешний ключ на нормативный документ
    livestatus - Признак действующего адресного объекта
    divtype - Тип адресации:
      0 - не определено
      1 - муниципальный;
      2 - административно-территориальный
    """

    aoguid = models.UUIDField()
    formalname = models.CharField(max_length=120)
    regioncode = models.CharField(max_length=2)
    autocode = models.CharField(max_length=1)
    areacode = models.CharField(max_length=3)
    citycode = models.CharField(max_length=3)
    ctarcode = models.CharField(max_length=3)
    placecode = models.CharField(max_length=3)
    plancode = models.CharField(max_length=4)
    streetcode = models.CharField(null=True, max_length=4)
    extrcode = models.CharField(max_length=4)
    sextcode = models.CharField(max_length=3)
    offname = models.CharField(null=True, max_length=120)
    postalcode = models.CharField(null=True, max_length=6)
    ifnsfl = models.CharField(null=True, max_length=4)
    terrifnsfl = models.CharField(null=True, max_length=4)
    ifnsul = models.CharField(null=True, max_length=4)
    terrifnsul = models.CharField(null=True, max_length=4)
    okato = models.CharField(null=True, max_length=11)
    oktmo = models.CharField(null=True, max_length=11)
    updatedate = models.DateField()
    shortname = models.CharField(max_length=10)
    aolevel = models.PositiveIntegerField()
    parentguid = models.UUIDField(null=True)
    aoid = models.UUIDField(primary_key=True)
    previd = models.UUIDField(null=True)
    nextid = models.UUIDField(null=True)
    prev = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='prevs')
    next = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='nexts')
    code = models.CharField(null=True, max_length=17)
    plaincode = models.CharField(null=True, max_length=15)
    actstatus = models.ForeignKey(ActualStatus, null=True, on_delete=models.PROTECT)  # PositiveIntegerField()
    centstatus = models.ForeignKey(CenterStatus, null=True, on_delete=models.PROTECT)  # PositiveIntegerField()
    operstatus = models.ForeignKey(OperationStatus, null=True, on_delete=models.PROTECT)  # PositiveIntegerField()
    currstatus = models.ForeignKey(CurrentStatus, null=True, on_delete=models.PROTECT)  # PositiveIntegerField()
    startdate = models.DateField()
    enddate = models.DateField()
    normdocid = models.UUIDField(null=True)
    normdoc = models.ForeignKey(NormativeDocument, null=True, on_delete=models.PROTECT)  # UUIDField(null=True)
    livestatus = models.PositiveIntegerField()
    divtype = models.PositiveIntegerField()

    class Meta:
        db_table = 'fias\".\"addrobj'


# House

class EstateStatus(models.Model):
    """
    Признак владения

    eststatid - Признак владения
    name - Наименование
    shortname - Краткое наименование
    """

    eststatid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    shortname = models.CharField(null=True, max_length=20)

    class Meta:
        db_table = 'fias\".\"eststat'


class StructureStatus(models.Model):
    """
    Признак строения

    strstatid - Признак строения
    name - Наименование
    shortname - Краткое наименование
    """

    strstatid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    shortname = models.CharField(null=True, max_length=20)

    class Meta:
        db_table = 'fias\".\"strstat'


class HouseStateStatus(models.Model):
    """
    Статус состояния домов

    housestid - Идентификатор статуса
    name - Наименование
    """

    housestid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=60)

    class Meta:
        db_table = 'fias\".\"hststat'


class House(models.Model):
    """
    Сведения по номерам домов улиц городов и населенных пунктов

    postalcode - Почтовый индекс
    regioncode - Код региона
    ifnsfl - Код ИФНС ФЛ
    terrifnsfl - Код территориального участка ИФНС ФЛ
    ifnsul - Код ИФНС ЮЛ
    terrifnsul - Код территориального участка ИФНС ЮЛ
    okato - OKATO
    oktmo - OKTMO
    updatedate - Дата время внесения записи
    housenum - Номер дома
    eststatus - Признак владения
    buildnum - Номер корпуса
    strucnum - Номер строения
    strstatus - Признак строения
    houseid - Уникальный идентификатор записи дома
    houseguid - Глобальный уникальный идентификатор дома
    aoguid - Guid записи родительского объекта (улицы, города, населенного пункта и т.п.)
    startdate - Начало действия записи
    enddate - Окончание действия записи
    statstatus - Состояние дома
    normdocid - UUID нормативного документа
    normdoc - Внешний ключ на нормативный документ
    counter - Счетчик записей домов для КЛАДР 4
    cadnum - Кадастровый номер
    divtype - Тип адресации:
        0 - не определено
        1 - муниципальный;
        2 - административно-территориальный
    """

    postalcode = models.CharField(null=True, max_length=6)
    regioncode = models.CharField(null=True, max_length=2)
    ifnsfl = models.CharField(null=True, max_length=4)
    terrifnsfl = models.CharField(null=True, max_length=4)
    ifnsul = models.CharField(null=True, max_length=4)
    terrifnsul = models.CharField(null=True, max_length=4)
    okato = models.CharField(null=True, max_length=11)
    oktmo = models.CharField(null=True, max_length=11)
    updatedate = models.DateField()
    housenum = models.CharField(null=True, max_length=20)
    eststatus = models.ForeignKey(EstateStatus, on_delete=models.PROTECT)  # PositiveIntegerField()
    buildnum = models.CharField(null=True, max_length=10)
    strucnum = models.CharField(null=True, max_length=10)
    strstatus = models.ForeignKey(StructureStatus, null=True, on_delete=models.PROTECT)  # PositiveIntegerField(null=True)
    houseid = models.UUIDField(primary_key=True)
    houseguid = models.UUIDField()
    aoguid = models.UUIDField()
    startdate = models.DateField()
    enddate = models.DateField()
    statstatus = models.ForeignKey(HouseStateStatus, on_delete=models.PROTECT)  # PositiveIntegerField()
    normdocid = models.UUIDField(null=True)
    normdoc = models.ForeignKey(NormativeDocument, null=True, on_delete=models.PROTECT)  # UUIDField(null=True)
    counter = models.PositiveIntegerField()
    cadnum = models.CharField(null=True, max_length=100)
    divtype = models.PositiveIntegerField()

    class Meta:
        db_table = 'fias\".\"house'


# Room

class FlatType(models.Model):
    """
    Тип помещения

    fltypeid - Тип помещения
    name - Наименование
    shortname - Краткое наименование
    """

    fltypeid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    shortname = models.CharField(null=True, max_length=20)

    class Meta:
        db_table = 'fias\".\"flattype'


class RoomType(models.Model):
    """
    Тип комнаты

    rmtypeid - Тип комнаты
    name - Наименование
    shortname - Краткое наименование
    """

    rmtypeid = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    shortname = models.CharField(null=True, max_length=20)

    class Meta:
        db_table = 'fias\".\"roomtype'


class Room(models.Model):
    """
    Классификатор помещениях

    roomguid - Глобальный уникальный идентификатор адресного объекта (помещения)
    flatnumber - Номер помещения или офиса
    flattype - Тип помещения
    roomnumber - Номер комнаты
    roomtype - Тип комнаты
    regioncode - Код региона
    postalcode - Почтовый индекс
    updatedate - Дата  внесения записи
    houseguid - Идентификатор родительского объекта (дома)
    roomid - Уникальный идентификатор записи. Ключевое поле.
    previd - Идентификатор записи связывания с предыдушей исторической записью
    nextid - Идентификатор записи  связывания с последующей исторической записью
    startdate - Начало действия записи
    enddate - Окончание действия записи
    livestatus - Признак действующего адресного объекта
    normdocid - UUID нормативного документа
    normdoc - Внешний ключ на нормативный документ
    operstatus - Статус действия над записью – причина появления записи (см. описание таблицы OperationStatus):
        01 – Инициация;
        10 – Добавление;
        20 – Изменение;
        21 – Групповое изменение;
        30 – Удаление;
        31 - Удаление вследствие удаления вышестоящего объекта;
        40 – Присоединение адресного объекта (слияние);
        41 – Переподчинение вследствие слияния вышестоящего объекта;
        42 - Прекращение существования вследствие присоединения к другому адресному объекту;
        43 - Создание нового адресного объекта в результате слияния адресных объектов;
        50 – Переподчинение;
        51 – Переподчинение вследствие переподчинения вышестоящего объекта;
        60 – Прекращение существования вследствие дробления;
        61 – Создание нового адресного объекта в результате дробления
    cadnum - Кадастровый номер помещения
    roomcadnum - Кадастровый номер комнаты в помещении
    """

    roomguid = models.UUIDField()
    flatnumber = models.CharField(max_length=50)
    flattypeid = models.PositiveIntegerField()
    flattype = models.ForeignKey(FlatType, on_delete=models.PROTECT, null=True)
    roomnumber = models.CharField(null=True, max_length=50)
    roomtype = models.ForeignKey(RoomType, null=True, on_delete=models.PROTECT)  # Возможно значение через поле "rmtype" в XML, PositiveIntegerField(null=True)
    regioncode = models.CharField(max_length=2)
    postalcode = models.CharField(null=True, max_length=6)
    updatedate = models.DateField()
    houseguid = models.UUIDField()
    roomid = models.UUIDField(primary_key=True)
    previd = models.UUIDField(null=True)
    nextid = models.UUIDField(null=True)
    prev = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='prevs')
    next = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='nexts')
    startdate = models.DateField()
    enddate = models.DateField()
    livestatus = models.PositiveIntegerField()
    normdocid = models.UUIDField(null=True)
    normdoc = models.ForeignKey(NormativeDocument, null=True, on_delete=models.PROTECT)  # UUIDField(null=True)
    operstatus = models.ForeignKey(OperationStatus, on_delete=models.PROTECT)  # PositiveIntegerField()
    cadnum = models.CharField(null=True, max_length=100)
    roomcadnum = models.CharField(null=True, max_length=100)

    class Meta:
        db_table = 'fias\".\"room'


# Stead

class Stead(models.Model):
    """
    Классификатор земельных участков

    steadguid - Глобальный уникальный идентификатор адресного объекта (земельного участка)
    number - Номер земельного участка
    regioncode - Код региона
    postalcode - Почтовый индекс
    ifnsfl - Код ИФНС ФЛ
    terrifnsfl - Код территориального участка ИФНС ФЛ
    ifnsul - Код ИФНС ЮЛ
    terrifnsul - Код территориального участка ИФНС ЮЛ
    okato - OKATO
    oktmo - OKTMO
    updatedate - Дата  внесения записи
    parentguid - Идентификатор объекта родительского объекта
    steadid - Уникальный идентификатор записи. Ключевое поле.
    previd - Идентификатор записи связывания с предыдушей исторической записью
    nextid - Идентификатор записи  связывания с последующей исторической записью
    operstatus - Статус действия над записью – причина появления записи (см. описание таблицы OperationStatus):
        01 – Инициация;
        10 – Добавление;
        20 – Изменение;
        21 – Групповое изменение;
        30 – Удаление;
        31 - Удаление вследствие удаления вышестоящего объекта;
        40 – Присоединение адресного объекта (слияние);
        41 – Переподчинение вследствие слияния вышестоящего объекта;
        42 - Прекращение существования вследствие присоединения к другому адресному объекту;
        43 - Создание нового адресного объекта в результате слияния адресных объектов;
        50 – Переподчинение;
        51 – Переподчинение вследствие переподчинения вышестоящего объекта;
        60 – Прекращение существования вследствие дробления;
        61 – Создание нового адресного объекта в результате дробления
    startdate - Начало действия записи
    enddate - Окончание действия записи
    normdocid - UUID нормативного документа
    normdoc - Внешний ключ на нормативный документ
    livestatus - Признак действующего адресного объекта
    cadnum - Кадастровый номер
    divtype - Тип адресации:
        0 - не определено
        1 - муниципальный;
        2 - административно-территориальный
    """

    steadguid = models.UUIDField()
    number = models.CharField(null=True, max_length=120)
    regioncode = models.CharField(max_length=2)
    postalcode = models.CharField(null=True, max_length=6)
    ifnsfl = models.CharField(null=True, max_length=4)
    terrifnsfl = models.CharField(null=True, max_length=4)
    ifnsul = models.CharField(null=True, max_length=4)
    terrifnsul = models.CharField(null=True, max_length=4)
    okato = models.CharField(null=True, max_length=11)
    oktmo = models.CharField(null=True, max_length=11)
    updatedate = models.DateField()
    parentguid = models.UUIDField(null=True)
    steadid = models.UUIDField(primary_key=True)
    previd = models.UUIDField(null=True)
    nextid = models.UUIDField(null=True)
    prev = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='prevs')
    next = models.ForeignKey('self', null=True, on_delete=models.PROTECT, related_name='nexts')
    operstatus = models.ForeignKey(OperationStatus, on_delete=models.PROTECT)  # PositiveIntegerField()
    startdate = models.DateField()
    enddate = models.DateField()
    normdocid = models.UUIDField(null=True)
    normdoc = models.ForeignKey(NormativeDocument, null=True, on_delete=models.PROTECT)  # UUIDField(null=True)
    livestatus = models.PositiveIntegerField()
    cadnum = models.CharField(null=True, max_length=100)
    divtype = models.PositiveIntegerField()

    class Meta:
        db_table = 'fias\".\"stead'


# Устаревшие (согласно документации):
# - HouseInterval
# - IntervalStatus (В документации явно не указано, но по всей видимости и это не нужно)
# - Landmark

# Не являются внешними ключами (ссылаются на ID физического объекта, не обязательно уникального):
# Object.parentguid
# House.aoguid
# Stead.parentguid

# Integer-ы, которые, как предполагается, должны были быть словорями, но, вроде как, являются интами
# - livestatus
# - divtype

# Баги XSD и XML:
# - roomtype в XSD, но rmtype в XML
# - не понятно куда должен вести этот внешний ключ - NormativeDocument.docimgid
# - Добавлен flattypeid для записи туда int flattype. Room.flattype в свою очередь будет использован позже для Foreign key.
# - FlatType с id = 10 не существует

# Иногда, записи в дельтах FIAS ссылаются на несуществующие normdoc-и
# Поэтому, всем моделям, у которых есть normdoc, добавлен normdocid = models.UUIDField(null=True) и,
# при загрузке дельты, записываем normdoc туда

# Комментарии справа от поля означают оригинальный тип данных, сгенерированный согласно XSD
# Если в XML у документа нет maxLength/length, используем - CharField
# Object, Stead, Room - должны быть зациклены сами на себе, поэтому, создаём им дополнительные два поля prev и next
