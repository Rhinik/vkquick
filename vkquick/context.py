from __future__ import annotations
import asyncio
import dataclasses
import typing as ty

from vkquick.wrappers.user import User
from vkquick.events_generators.event import Event
from vkquick.utils import AttrDict, random_id as random_id_
from vkquick.base.handling_status import HandlingStatus
from vkquick.shared_box import SharedBox
from vkquick.api import API


class _MessagesSendResponse:
    """
    Для ответов, содержащих поля peer_ids
    """

    peer_id: int
    message_id: int
    conversation_message_id: int


@dataclasses.dataclass
class Context:

    shared_box: SharedBox
    source_event: Event
    filters_response: ty.Dict[str, HandlingStatus] = dataclasses.field(
        default_factory=dict
    )
    extra: AttrDict = dataclasses.field(default_factory=AttrDict)

    @property
    def msg(self):
        return self.source_event.message

    @property
    def api(self) -> API:
        """
        Текущий инстанс API, который был передан
        при инициализации бота
        """
        return self.shared_box.api

    async def answer(
        self,
        message: ty.Optional[str] = None,
        /,
        *,
        random_id: ty.Optional[int] = None,
        lat: ty.Optional[float] = None,
        long: ty.Optional[float] = None,
        attachment: ty.Optional[ty.List[str]] = None,
        reply_to: ty.Optional[int] = None,
        forward_messages: ty.Optional[ty.List[int]] = None,
        sticker_id: ty.Optional[int] = None,
        group_id: ty.Optional[int] = None,
        keyboard: ty.Optional[str] = None,
        payload: ty.Optional[str] = None,
        dont_parse_links: ty.Optional[bool] = None,
        disable_mentions: ty.Optional[bool] = None,
        intent: ty.Optional[str] = None,
        expire_ttl: ty.Optional[int] = None,
        silent: ty.Optional[bool] = None,
        subscribe_id: ty.Optional[int] = None,
        content_source: ty.Optional[str] = None,
        forward: ty.Optional[str] = None,
        **kwargs,
    ) -> _MessagesSendResponse:
        """
        Отправляет сообщение в тот же диалог/беседу,
        откуда пришло. Все поля соответствуют
        методу `messages.send`
        """
        params = {"peer_ids": self.msg.peer_id}
        return await self._send_message_via_local_kwargs(locals(), params)

    async def reply(
        self,
        message: ty.Optional[str] = None,
        /,
        *,
        random_id: ty.Optional[int] = None,
        lat: ty.Optional[float] = None,
        long: ty.Optional[float] = None,
        attachment: ty.Optional[ty.List[str]] = None,
        sticker_id: ty.Optional[int] = None,
        group_id: ty.Optional[int] = None,
        keyboard: ty.Optional[str] = None,
        payload: ty.Optional[str] = None,
        dont_parse_links: ty.Optional[bool] = None,
        disable_mentions: ty.Optional[bool] = None,
        intent: ty.Optional[str] = None,
        expire_ttl: ty.Optional[int] = None,
        silent: ty.Optional[bool] = None,
        subscribe_id: ty.Optional[int] = None,
        content_source: ty.Optional[str] = None,
        **kwargs,
    ) -> _MessagesSendResponse:
        """
        Отвечает на сообщение, которым была вызвана команда.
        Все поля соответствуют методу `messages.send`
        """
        params = {
            "peer_ids": self.msg.peer_id,
            "forward": {
                "is_reply": True,
                "conversation_message_ids": [
                    self.msg.conversation_message_id
                ],
                "peer_id": self.msg.peer_id,
            },
        }
        return await self._send_message_via_local_kwargs(locals(), params)

    async def forward(
        self,
        message: ty.Optional[str] = None,
        /,
        *,
        random_id: ty.Optional[int] = None,
        lat: ty.Optional[float] = None,
        long: ty.Optional[float] = None,
        attachment: ty.Optional[ty.List[str]] = None,
        sticker_id: ty.Optional[int] = None,
        group_id: ty.Optional[int] = None,
        keyboard: ty.Optional[str] = None,
        payload: ty.Optional[str] = None,
        dont_parse_links: ty.Optional[bool] = None,
        disable_mentions: ty.Optional[bool] = None,
        intent: ty.Optional[str] = None,
        expire_ttl: ty.Optional[int] = None,
        silent: ty.Optional[bool] = None,
        subscribe_id: ty.Optional[int] = None,
        content_source: ty.Optional[str] = None,
        **kwargs,
    ) -> _MessagesSendResponse:
        """
        Пересылает сообщение, которым была вызвана команда.
        Все поля соответствуют методу `messages.send`
        """
        params = {
            "peer_ids": self.msg.peer_id,
            "forward": {
                "conversation_message_ids": [
                    self.msg.conversation_message_id
                ],
                "peer_id": self.msg.peer_id,
            },
        }
        return await self._send_message_via_local_kwargs(locals(), params)

    async def fetch_replied_message_sender(
        self,
        fields: ty.Optional[ty.List[str]] = None,
        name_case: ty.Optional[str] = None,
    ) -> ty.Optional[User]:
        """
        Возвращает специальную обертку на пользователя
        из replied-сообщения. Если такого нет, то вернется None.
        Получение пользователя использует кэширование.
        Аргументы этой функции будут переданы в `users.get`
        """
        if self.msg.reply_message is None:
            return None

        user_id = self.msg.reply_message.from_id
        user = await self.api.fetch_user_via_id(
            user_id, fields=fields, name_case=name_case
        )
        return user

    async def fetch_forward_messages_sender(
        self,
        fields: ty.Optional[ty.List[str]] = None,
        name_case: ty.Optional[str] = None,
    ) -> ty.List[User]:
        """
        Возвращает список людей из пересланных
        сообщений специальными обертками.
        Если таких нет, то вернется пустой список.
        Получение пользователя использует кэширование.
        Аргументы этой функции будут переданы в `users.get`
        на каждого пользователя
        """
        user_tasks = []
        for message in self.msg.fwd_messages:
            user_task = await self.api.fetch_user_via_id(
                message.from_id, fields=fields, name_case=name_case
            )
            user_tasks.append(user_task)
        users = await asyncio.gather(*user_tasks)
        return users

    async def fetch_attached_user(
        self,
        fields: ty.Optional[ty.List[str]] = None,
        name_case: ty.Optional[str] = None,
    ) -> ty.Optional[User]:
        """
       Возвращает обертку на "прикрепленного пользователя".
       Если есть replied-сообщение -- вернется отправитель того сообщения,
       если есть пересланное сообщение -- отправитель первого прикрепленного сообщения.
       Если ни того, ни другого нет, вернется `None`.
       Получение пользователя использует кэширование.
       Аргументы этой функции будут переданы в `users.get`
       """
        replied_user = await self.fetch_replied_message_sender(
            fields=fields, name_case=name_case
        )
        if replied_user is not None:
            return replied_user
        if not self.msg.fwd_messages:
            return None
        first_user_from_fwd = await self.api.fetch_user_via_id(
            self.msg.fwd_messages[0].from_id,
            fields=fields,
            name_case=name_case,
        )
        return first_user_from_fwd

    async def fetch_sender(
        self,
        fields: ty.Optional[ty.List[str]] = None,
        name_case: ty.Optional[str] = None,
    ) -> User:
        """
        Специальной оберткой возвращает пользователя,
        который отправил сообщение.
        Получение пользователя использует кэширование.
        Аргументы этой функции будут переданы в `users.get`
        """
        sender = await self.api.fetch_user_via_id(
            self.msg.from_id, fields=fields, name_case=name_case
        )
        return sender

    def get_photos(self):
        ...

    def get_docs(self):
        ...

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(source_event, message, client_info, "
            f"filters_response, extra)"
        )

    async def _send_message_via_local_kwargs(
        self, local_kwargs, pre_params
    ) -> _MessagesSendResponse:
        """
        Вспомогательная функция для методов,
        реализующих отправку сообщений (reply. answer).
        Фильтрует аргументы, которые были переданы при вызове этого метода
        """
        for name, value in local_kwargs.items():
            if name == "kwargs":
                pre_params.update(value)
            elif name != "self" and value is not None:
                pre_params.update({name: value})

        del pre_params["params"]

        if local_kwargs["random_id"] is None:
            pre_params["random_id"] = random_id_()

        response = await self.api.method("messages.send", pre_params)
        return response[0]
