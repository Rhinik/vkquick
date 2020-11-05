"""
Union argument
"""
import warnings
import typing as ty

from vkquick.base import text_cutter
import vkquick.utils


class Union(text_cutter.TextCutter):
    """
    Один из вариантов `TextArgument`. Если вариант
    не подходит под первый тип, будет пробовать следующий.
    Если все не подошли -- значит парсинг строки не удался
    и команда не вызовется
    """

    def __init__(self, *text_arguments):
        self.available_type = text_arguments
        self._check_passed(text_arguments)

    @staticmethod
    def _check_passed(text_arguments):
        if len(text_arguments) == 0:
            raise ValueError("Union type must contains at least 2 types")
        elif len(text_arguments) == 1:
            warnings.warn(
                "Union type contains only one type. The expression can be shortened",
                UserWarning,
            )

    async def cut_part(self, arguments_string: str) -> ty.Tuple[ty.Any, str]:
        for type_ in self.available_type:
            values = await vkquick.utils.sync_async_run(
                type_.cut_part(arguments_string)
            )
            if values[0] is not text_cutter.UnmatchedArgument:
                return values
        return text_cutter.UnmatchedArgument, arguments_string

    def usage_description(self) -> str:
        description = "Аргумент должен подходить под одно из описаний:\n"
        for ind, value in enumerate(self.available_type, 1):
            value_description = value.usage_description()
            description += f"{ind}) {value_description} "

        return description