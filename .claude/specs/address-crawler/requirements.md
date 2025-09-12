# Requirements Document

## Introduction

地址爬虫功能将构建一个自动化的地址信息采集系统，通过定时任务从指定的API接口获取地址数据，并存储到MySQL数据库中。该功能专注于实现简单易用的核心爬虫功能，为地址数据收集提供基础支撑。

## Alignment with Product Vision

此功能完全符合产品愿景中的关键要素：
- **简单优先**: 采用Flask + SQLAlchemy的简洁架构，避免过度设计
- **功能完整**: 实现从API调用到数据存储的完整爬虫流程
- **易于维护**: 模块化设计，代码结构清晰，便于后续扩展

通过实现定时爬虫任务，该功能将自动化地址数据采集流程，减少人工干预，提高数据收集效率。

## Requirements

### Requirement 1: 基础爬虫功能

**User Story:** 作为系统管理员，我想要系统能够自动从API获取地址数据，以便无需手动操作就能收集地址信息。

#### Acceptance Criteria

1. WHEN 爬虫任务被触发 THEN 系统 SHALL 向 https://www.meiguodizhi.com/api/v1/dz 发送HTTP GET请求
2. IF API返回状态码为200 THEN 系统 SHALL 解析JSON响应数据，格式为：{"address": {"Address": "...", "Telephone": "...", "City": "...", "Zip_Code": "...", "State": "...", "State_Full": "..."}, "status": "ok"}
3. WHEN 成功获取地址数据 THEN 系统 SHALL 提取address、telephone、city、zip_code、state、state_full字段
4. WHEN API返回其他错误状态码 THEN 系统 SHALL 记录错误信息并跳过当前任务

### Requirement 2: 数据存储功能

**User Story:** 作为数据管理员，我想要系统能够将爬取到的地址信息保存到数据库，以便后续查询和使用。

#### Acceptance Criteria

1. WHEN 爬虫成功获取地址数据 THEN 系统 SHALL 将数据保存到address_info表，包含字段：address、telephone、city、zip_code、state、state_full、country、source_url、created_at、updated_at
2. IF 数据保存失败 THEN 系统 SHALL 记录错误日志并继续执行下一个任务
3. WHEN 数据保存成功 THEN 系统 SHALL 记录成功日志并更新任务状态
4. IF 检测到重复地址（相同address和telephone） THEN 系统 SHALL 跳过保存并记录跳过的数据
5. WHEN 必填字段（address、telephone）为空 THEN 系统 SHALL 跳过保存并记录验证错误

### Requirement 3: 任务调度功能

**User Story:** 作为系统维护人员，我想要系统能够每秒自动执行爬虫任务，以便持续收集地址数据。

#### Acceptance Criteria

1. WHEN 系统启动时 THEN 系统 SHALL 初始化APScheduler并配置每秒执行的任务
2. IF 存在未完成的任务(visited_num < total_num) THEN 系统 SHALL 选择第一个任务执行
3. WHEN 任务执行完成后 THEN 系统 SHALL 更新visited_num字段+1，如visited_num >= total_num则标记任务完成
4. IF 任务执行过程中发生异常 THEN 系统 SHALL 记录异常信息并继续执行其他任务
5. WHEN 没有待执行任务时 THEN 系统 SHALL 记录空闲状态并等待下一秒调度

### Requirement 4: 任务管理功能

**User Story:** 作为任务管理员，我想要能够创建和管理爬虫任务，以便控制数据收集的范围和频率。

#### Acceptance Criteria

1. WHEN 创建新任务时 THEN 系统 SHALL 接受url、method、total_num、body、headers、timeout参数，其中timeout默认值为30秒
2. IF 任务参数验证失败（如total_num <= 0） THEN 系统 SHALL 返回错误信息并拒绝创建任务
3. WHEN 查询任务状态时 THEN 系统 SHALL 返回任务的当前状态、已执行次数、总次数、创建时间和更新时间
4. IF 任务已完成(visited_num >= total_num) THEN 系统 SHALL 将状态标记为"completed"
5. WHEN 任务正在执行时 THEN 系统 SHALL 将状态标记为"running"

### Requirement 5: 日志记录功能

**User Story:** 作为系统运维人员，我想要系统能够记录运行日志，以便监控爬虫执行状态和排查问题。

#### Acceptance Criteria

1. WHEN 系统运行时 THEN 系统 SHALL 记录所有关键操作（任务开始、成功、失败、跳过）
2. IF 发生异常 THEN 系统 SHALL 记录异常信息、堆栈跟踪和上下文数据
3. WHEN 日志文件达到10MB时 THEN 系统 SHALL 自动轮转日志文件，保留最近7天的日志
4. IF API限流发生时 THEN 系统 SHALL 记录限流信息和重试次数
5. WHEN 数据验证失败时 THEN 系统 SHALL 记录验证失败的具体原因和相关数据

### Requirement 6: 数据验证和质量控制

**User Story:** 作为数据管理员，我想要系统能够验证和保证数据质量，以确保收集到的地址信息准确可用。

#### Acceptance Criteria

1. WHEN 保存地址数据前 THEN 系统 SHALL 验证必填字段（address、telephone）不为空且格式正确
2. IF address字段长度超过1024字符 THEN 系统 SHALL 截断至1024字符并记录警告
3. IF telephone字段包含非数字字符 THEN 系统 SHALL 移除非法字符并记录处理信息
4. WHEN 检测到重复地址（相同address和telephone组合） THEN 系统 SHALL 跳过保存并记录跳过的原因

### Requirement 7: 系统监控和状态报告

**User Story:** 作为系统运维人员，我想要系统能够提供运行状态报告，以便监控整体健康状况。

#### Acceptance Criteria

1. WHEN 系统运行时 THEN 系统 SHALL 每分钟输出一次统计信息（成功任务数、失败任务数、跳过任务数）
2. IF 连续失败任务数超过10个 THEN 系统 SHALL 输出警告信息并建议检查API可用性