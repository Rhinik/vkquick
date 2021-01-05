Валидаторы в использовании представляют собой просто висящие декораторы над реакциями (Важно: они должны быть выше декоратора `Reaction`) и на каждое подходящее событие проверяют, подходит ли команда по более конкретным условиям, например, попадает ли текстовая команда пользователя под шаблон заданной, зашел ли пользователь в беседу, или же вышел, имеет ли пользователь права на эту команду и прочее. Вместо того, чтобы городить кучу if'ов, достаточно просто повесить декоратор с нужными настройками. Помимо всего остального, валидаторы могут быть вызваны в async, и они всегда имеют одинаковый набор _необходимых_ аргументов, что делает их совместимой с __любой__ реакцией


!!! Example
    Команда сработает, если ее имя одно из `names` и префикс один из `prefs`, т.е. это __валидные__ вызовы команды:

    * `/info`
    * `!info`
    * `/инфо`
    * `!инфо`

    ```python
    import vkquick as vq


    @vq.Cmd(
        names=["info", "инфо"],
        prefs=["!", "/"]
    )
    @vq.Reaction("message_new")
    def info(sender: vq.Sender()):
        return f"Your name is {sender.fn} and last name is {sender.ln}"
    ```

!!! Example
    Команда сработает, если пользователь вышел из беседы
    ```python
    import vkquick as vq


    @vq.Action("chat_leave_user")
    @vq.Reaction("message_new")
    def leave_chat():
        return f"Someone left us!"
    ```

## Валидаторы из коробки
Все валидаторы можно получить, обращаясь к модулю `vkquick`, т.е. `vq.Cmd`, `vq.Action`

### `Cmd`
Обработчик текстовой команды. Принимает в себя следующие аргументы при инициализации:

Поле|Тип|Значение по умолчанию|Описание
-|-|-|-
`prefs`|List[str]|Нет префиксов|Возможные префиксы команды. Стоят в самом ее начале
`names`|str|Нет имен. Да, в совокупности с пустым префиксом и отсутствием аргументов это бесполезный валидатор. Можете смело убирать его в таком кейсе|Возможные имена команды. Идут __вплотную__ к префиксу
`sensetive`|bool|False|Должна ли команда быть чувствительной к регистру символов|
`argline`|str|По умолчанию не используется|Изначально все __аргументы__ команды разделяются `r"\s+"`, но вы можете в корне поменять схему линии аргументов, используя _ленивую_ интерполяцию. Например, пользователь должен ввести имя какого-то человека и через двоеточие число (`/com Bob:56`). Реакция будет выглядеть как на примере ниже

!!! Example "Пример использовани параметра `argline`"
    ```python
    import vkquick as vq


    @vq.Cmd(
        prefs=["/"],
        names=["com"],
        argline="\s+{name}:{num}"
    )
    @vq.Reaction("message_new")
    def com(name: vq.Word(), num: int):
        ...
    ```

#### О получении аргументов команды
Наверно, самая важная и самая актуальная тема. Если вы обратили внимание на пример выше, то заметили новый `vq.Word` и ~~внезапно~~ built-it класс `int`. И так, как же это работает

Для того, чтобы указать, что у команды есть какой-то аргумент (какое-то упоминание, число и прочее), нужно использовать соответствующий класс, унаследованный от `vq.CommandArgument`, в аннотациях. Например, команда, принимающая __слово__ и __число__ будет выглядеть так

```python
import vkquick as vq


@vq.Cmd(names=["foo"])
@vq.Reaction("message_new")
def foo(val: vq.Word(), num: vq.Integer()):
    return f"{val=} {num=}"
```

Пример вызова|Возвращаемое значение
-|-
`/foo abcde 456`|`val='abcde' num=456`
`/foo fiz123z 456789`|`val='fiz123z' num=456789`

!!! Note
    Заметьте, что `vq.Integer` сразу вернул число, посколько строка обернулась в поле __factory__. О нем чуть ниже

Я думаю, что достаточно очевидно, как этим пользоваться — просто обозначаешь нужные аргументы __нужными__ типами (о них ниже). Но что насчет payload-типов? Вы можете без проблем использовать и то, и другое в аргументах функции. __vkquick__ поймет, что для чего. Например, код выше, но с использованием `vq.Sender()`

```python
import vkquick as vq


@vq.Cmd(names=["foo"])
@vq.Reaction("message_new")
def foo(val: vq.Word(), num: vq.Integer(), sender: vq.Sender()):
    return f"{sender.fn}, {val=} {num=}"
```

Теперь команда при ответе добавит имя отправителя в начале сообщения

И, конечно же, слово и число — не единственные типы. ~~Вот они по порядку, слева направо: ворд, интегер, юзверьменьшион...~~

Имя|Фабрика, в которую обернется значение|Регулярные выражение|Описание
-|-|-|-
`Integer`|`int`|`\d+`|__Целое__ число. Можете использовать `int` в аннотациях (что-то на подобие аллиасного типа). Эффект тот же. Скобки ставить тогда не нужно
`String`|`str`|`.+`|Строка, состоящая как из пробельных, так и непробельных символов. Как и с `Integer`, для этого типа можно использовать `str` (тоже без скобок)
`Word`|`str`|`\S+`|Слово, содержащее любые символы, кроме пробельных. Тобишь `foo`, `foo123`, `&foo)90` — слова, а вот `foo bar` — нет, это уже 2 слова
`List`|`list`|-|Список каких-либо `CommandArgument`. Принимает аргументы: `sep` для разделителя, по умолчанию `(?:\s*,\s*|\s+)`, `min_` (1) и `max_` (не ограничено, `Ellipsis`) для минимального и максимального количества элементов. Вы также можете просто обернуть тип в квадратные скобки, и он будет списковым, тобишь `[int]` — это аналог `List(Integer())`
`UserMention`|`User`|`\[id\d+\|.+?\]`|Упоминание __пользователя__. Работает исключительно на упоминание, тобишь ни ссылки, ни просто цифры ID не сработают (скорее всего такая поддержка будет чуть позже). Принимает в себя поля‘ для по‘ля `fields` метода `users.get`, т.к. возвращает объект пользователя
`Literal`|`str`|-|Своего рода Enum, аналог `typing.Literal`, т.е. набор определенных значений. Например, `Literal("foo", "bar")` означает `(?:foo|bar)`
`Custom`|-|-|Делает тип по регулярному выржанию из первого аргумента и фабрике из второго
`Optional`|-|-|Делает тип опциональным. Принимает заменитель, который будет возвращен в случае, если пользователь не передал аргумент в тексте


!!! Warning
    `vq.CommandArgument` (все типы из таблицы) __всегда__ должны быть инстансами, тобишь всегда иметь скобки в аннотациях

!!! Note
    `names`, `prefs` и `argline` поддерживают синтаксис регулярных выражений, поэтому будьте аккуратны, если используете, например, `+` не как квантификатор, а как символ, тобишь вместо `prefs=["+"]` нужно `prefs=["\+"]`

!!! Question "Зачем нужны префиксы для команд?"
    Префиксы для команды спасают от _нежелательных_ и _случайных_ вызовов команд. Более того, уникальный префикс является некой отличительной чертой ваше бота ;P

    Но не перемудрите. Префиксный символ должен быть легко печатаем на клавиатуре и компуктеров, и мобильников

#### Кастомный аргумент для текстовой команды
Чтобы создать свой собственный Cmd-тип, унаследуйтесь от `vq.CommandArgument` и определите следующее:

* Поле `rexp`, содержащее регулярное выражение, которому соотвествует тип. Если регулярка динамична, укажите `""`, но при этом вам нужно будет определить инициализатор, в котром укажете `self.rexp`
* Callable поле/метод (async/sync) `factory`, которое принимает один аргумент — строковое представление аргумента из текста, и, соответственно, возвращает нужный тип. Используйте его в своем `prepare`. Сделано для совместимсоти с типом `List`
* Async/sync метод `prepare`, который вызывается у аргумента перед тем, как тот попадет вызов. Должен вернуть соответствующее значение (оберните его в `factory`)
    Принимает следующие поля
    * `argname`: Имя аргумента, на которое будет привязано значение
    * `event`: Событие LongPoll, с которым был связан вызов реакции
    * `func`: Reaction-объект вашего обработчика
    * `bin_stack`: Пустышка для дополнительных промежуточных полей. Используйте для испобежания гонки данных.

Примеры типов можно найти [тут](https://github.com/Rhinik/vkquick/blob/master/vkquick/annotypes/command_types.py)


### Action
Принимает в себя \*список обрабатываемых `event.object.message.action.type` (Приглашение в беседу, выход, закрепление сообщения и прочее)

!!! todo
    Планируюется добавить быстрое получение пользователя из `member_id`

### ChatOnly
Сообщение пользователя должно быть отправленно только в беседе

### DirectOnly
Сообщение пользователя должно быть отправленно только в лс

## Кастомный валидатор
Для кастомного валидатора нужно унаследоваться от `vq.Validator` и определить async/sync метод `isvalid` (он вызывается для проверки для проверки валидности команды), принимающий следующие параметры

* `event`: Событие LongPoll
* `com`: Объект команды
* `bin_stack`: Поле, присутствующее только среди
проверки одной реакции на валидность и подготовки аргументов.
Помогает избегать гонку данных

После чего внутри функции указать `return`'ы, возвращающие следующие кортежы

0. `True`/`False`, в зависимости от того, валидна ли реакция
1. Описание-подсказка, используемое в дебаггере для отображения состояния валидатора