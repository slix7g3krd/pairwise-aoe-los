"""第 59 批：手雷在墙后爆炸，墙另一侧的角色掉了半管血，站在掩体后的坦克却没事...

范围伤害（AOE）判定修复模块，覆盖 13 个修复点：
视线遮挡、多层查询、掩体衰减、阵营规则、爆心回退、服务器权威、
动态查询、叠加上限、多射线采样、材质系数、格子去重、延迟一致、事件幂等。
"""


def los_blocked(blocked):
    """视线遮挡判定：爆心到目标的连线上存在任何遮挡物即判定被阻挡。

    :param blocked: 遮挡射线命中结果（真值表示存在遮挡）
    :return: True 表示视线被墙/掩体阻断，目标不承受直线伤害
    """
    return bool(blocked)


def layer_count(layers):
    """多层查询计数：逐楼层检查碰撞，返回命中（被占用/有遮挡）的层数。

    多层建筑不能只查一层，否则楼下爆炸会波及楼上；这里对每一层的
    碰撞结果独立计数，由调用方决定跨层伤害是否成立。

    :param layers: 各楼层碰撞结果的可迭代对象，真值表示该层有命中
    :return: 命中的楼层数量
    """
    return sum(1 for hit in layers if hit)


def cover_attenuation(distance, cover):
    """掩体衰减：伤害沿掩体传播时按掩体衰减系数折减。

    :param distance: 进入计算的基础伤害/距离量
    :param cover: 掩体衰减系数（0.0 完全吸收，1.0 无衰减）
    :return: 折减后的量，开阔地 cover=1.0 时不衰减
    """
    return distance * cover


def friendly_fire(team_a, team_b):
    """阵营判定：仅当双方属于不同阵营时开火/承伤才合法。

    :return: True 表示敌我不同阵营（可造成伤害），False 表示同阵营（误伤被拦截）
    """
    return team_a != team_b


def fallback_center(center, visible):
    """爆心回退：真实爆心被物体挡住不可见时，回退到最近的可见点。

    :param center: 原始爆炸中心
    :param visible: 最近可见点；None 表示没有遮挡、原爆心可见
    :return: 实际用于伤害判定的爆心
    """
    return visible if visible is not None else center


def server_authority(local, server):
    """服务器权威：爆炸位置与判定以服务器结果为准，客户端本地结果仅作预测。

    :param local: 客户端本地计算值
    :param server: 服务器权威值
    :return: 服务器值，保证延迟下两端判定一致
    """
    return server


def dynamic_query(inside, dynamic):
    """动态物体查询：静态网格初查或动态补查任一命中即判定目标在范围内。

    网格只查询一次会漏掉后进入范围的动态物体，因此动态补查命中也要计入。

    :param inside: 静态网格查询是否命中
    :param dynamic: 动态物体补查是否命中
    :return: True 表示目标应承受本次范围伤害
    """
    return bool(inside or dynamic)


def stack_cap(damage, cap):
    """叠加上限：多个爆炸同时命中时，总伤害不超过单帧伤害上限，防止瞬间秒杀。

    :param damage: 叠加后的原始伤害
    :param cap: 允许的最大伤害
    :return: 截断后的伤害
    """
    return min(damage, cap)


def multi_ray_score(hits):
    """多射线采样：对角色胶囊体打多条射线，按未被遮挡射线的比例给分。

    只打一条射线时角色边缘露出一点就会吃全额伤害；多射线按可见比例
    折算，边缘暴露只承受部分伤害。

    :param hits: 每条射线的命中/可见结果序列，真值表示该射线未被遮挡
    :return: 可见射线占比，范围 [0.0, 1.0]；空序列返回 0.0
    """
    if not hits:
        return 0.0
    return sum(1 for hit in hits if hit) / len(hits)


def material_factor(base, factor):
    """材质系数：可破坏物体与角色使用各自独立的材质系数，不再共用一套伤害表。

    :param base: 基础伤害
    :param factor: 目标材质对应的伤害系数
    :return: 乘算材质系数后的伤害
    """
    return base * factor


def grid_dedupe(cells):
    """格子去重：范围查询跨格子边界时对目标去重，避免边缘目标被重复计数。

    :param cells: 查询命中的格子/目标标识序列，可能含重复
    :return: 去重后的唯一格子数量
    """
    return len(set(cells))


def lag_state(current, past):
    """延迟一致：延迟补偿把目标倒带到过去位置时，掩体状态也必须取同一历史帧。

    掩体状态用当前帧会与倒带后的目标位置不一致，因此统一返回历史状态。

    :param current: 当前帧状态（不用于判定）
    :param past: 与倒带位置同帧的历史状态
    :return: 历史帧状态
    """
    return past


def event_idempotent(event_id, seen):
    """事件幂等：每个伤害事件带唯一幂等键，重试/重放不会重复扣血。

    :param event_id: 本次伤害事件的唯一标识
    :param seen: 已经处理过的事件标识集合
    :return: True 表示新事件、应当结算；False 表示重复事件、必须丢弃
    """
    return event_id not in seen
