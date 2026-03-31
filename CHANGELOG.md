# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **BREAKING**: `OpenAILikeChatClient` now uses Chat Completions API instead of Responses API
  - Renamed to `OpenAILikeChatCompletionClient` for clarity
  - `OpenAILikeChatClient` remains as backward compatibility alias
  - Inherits from `OpenAIChatCompletionClient` instead of `OpenAIChatClient`
  - Compatible with domestic LLMs (DeepSeek, Kimi, Qwen) that use `message.reasoning_content`
- Added `agent-framework-openai>=1.0.0rc6` as explicit dependency
- Added `pytest-recording` and `vcrpy` for integration testing

### Fixed

- Reasoning content extraction now works correctly with Chat Completions API
  - `_extract_reasoning_from_response` handles `message.reasoning_content` (non-streaming)
  - `_extract_reasoning_from_update` handles `delta.reasoning_content` (streaming)

## [0.1.7] - 2025-03-XX

### Added

- Initial release with OpenAI-like client extensions
- Docker-based code executor
- Dynamic skills provider