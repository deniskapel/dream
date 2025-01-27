import logging
from typing import Callable

from scenario.condition import get_current_user_id, graph
from df_engine.core import Context, Actor

logger = logging.getLogger(__name__)
# ....


def execute_response(
    ctx: Context,
    actor: Actor,
) -> Context:
    """Execute the callable response preemptively,
    so that slots can be filled"""
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    if callable(processed_node.response):
        processed_node.response = processed_node.response(ctx, actor)
    ctx.a_s["processed_node"] = processed_node

    return ctx


def set_flag(label: str, value: bool = True) -> Callable:
    """Sets a flag, modified coronavirus skill"""

    def set_flag_handler(ctx: Context, actor: Actor) -> Context:
        ctx.misc["flags"] = ctx.misc.get("flags", {})
        ctx.misc["flags"].update({label: value})
        return ctx

    return set_flag_handler


def fill_responses_by_slots_from_graph():
    def fill_responses_by_slots_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        user_id = get_current_user_id(ctx, actor)
        current_user_id = "User/" + user_id
        user_existing_entities = graph.get_properties_of_entity(entity_id=current_user_id)
        entity = "LIKE FOOD"
        entity_type = entity + "/Food"
        entity_with_id = user_existing_entities[entity_type][-1]
        logger.info(f"entity_with_id -- {entity_with_id}")
        slot_value = graph.get_properties_of_entity(entity_with_id)["substr"]
        logger.info(f"slot_value -- {slot_value}")
        processed_node.response = processed_node.response.replace("{" f"{entity}" "}", slot_value)
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return fill_responses_by_slots_processing
