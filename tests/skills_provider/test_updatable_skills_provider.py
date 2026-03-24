"""Tests for skills_provider module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_framework_ep.skills_provider import UpdatableSkillsProvider


class TestUpdatableSkillsProvider:
    """Tests for UpdatableSkillsProvider class."""

    def test_init_without_updater(self) -> None:
        """Test initialization without skills_updater."""
        provider = UpdatableSkillsProvider()

        assert provider._skills_updater is None

    def test_init_with_updater(self) -> None:
        """Test initialization with skills_updater."""

        async def mock_updater():
            return []

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        assert provider._skills_updater is mock_updater

    def test_init_with_skill_paths(self, tmp_path) -> None:
        """Test initialization with skill_paths."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # SKILL.md is required for skill discovery
        (skills_dir / "SKILL.md").write_text("# Test Skill")

        provider = UpdatableSkillsProvider(skill_paths=str(skills_dir))

        # Skills are loaded from paths but path itself is not stored
        assert isinstance(provider._skills, dict)

    @pytest.mark.asyncio
    async def test_update_with_updater_adds_skills(self) -> None:
        """Test _update adds skills from updater."""
        mock_skill = MagicMock()
        mock_skill.name = "test-skill"
        mock_skill.scripts = None

        async def mock_updater():
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        await provider._update()

        assert "test-skill" in provider._skills
        assert provider._skills["test-skill"] == mock_skill

    @pytest.mark.asyncio
    async def test_update_without_updater_does_nothing(self) -> None:
        """Test _update does nothing when no updater is set."""
        provider = UpdatableSkillsProvider()

        # Should not raise
        await provider._update()

        assert len(provider._skills) == 0

    @pytest.mark.asyncio
    async def test_update_logs_exception_on_failure(self, caplog) -> None:
        """Test _update logs error when updater fails."""

        async def failing_updater():
            raise ValueError("Updater failed")

        provider = UpdatableSkillsProvider(skills_updater=failing_updater)

        with caplog.at_level("ERROR"):
            await provider._update()

        assert "Failed to update skills" in caplog.text
        assert "Updater failed" in caplog.text

    @pytest.mark.asyncio
    async def test_update_continues_after_failure(self) -> None:
        """Test execution continues even when updater fails."""

        async def failing_updater():
            raise ValueError("Updater failed")

        provider = UpdatableSkillsProvider(skills_updater=failing_updater)

        # Should not raise
        await provider._update()

        # Provider should still be functional
        assert hasattr(provider, "_skills")

    @pytest.mark.asyncio
    async def test_before_run_calls_update(self) -> None:
        """Test before_run triggers skill update."""
        mock_skill = MagicMock()
        mock_skill.name = "dynamic-skill"
        mock_skill.scripts = None

        async def mock_updater():
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        # Mock the parent class's before_run
        with patch.object(
            provider.__class__.__bases__[0],
            "before_run",
            new_callable=AsyncMock,
        ) as mock_super_before_run:
            await provider.before_run(
                agent=MagicMock(),
                session=MagicMock(),
                context=MagicMock(),
                state=MagicMock(),
            )

        # Verify skill was added
        assert "dynamic-skill" in provider._skills
        # Verify parent's before_run was called
        mock_super_before_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_merges_skills(self) -> None:
        """Test _update merges new skills with existing ones."""
        mock_skill1 = MagicMock()
        mock_skill1.name = "skill-1"
        mock_skill1.scripts = None

        mock_skill2 = MagicMock()
        mock_skill2.name = "skill-2"
        mock_skill2.scripts = None

        call_count = 0

        async def mock_updater():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_skill1]
            return [mock_skill2]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        # First update
        await provider._update()
        assert "skill-1" in provider._skills
        assert "skill-2" not in provider._skills

        # Second update
        await provider._update()
        assert "skill-1" in provider._skills
        assert "skill-2" in provider._skills

    @pytest.mark.asyncio
    async def test_update_overwrites_existing_skill(self) -> None:
        """Test _update overwrites skill with same name."""
        mock_skill_v1 = MagicMock()
        mock_skill_v1.name = "my-skill"
        mock_skill_v1.description = "Version 1"
        mock_skill_v1.scripts = None

        mock_skill_v2 = MagicMock()
        mock_skill_v2.name = "my-skill"
        mock_skill_v2.description = "Version 2"
        mock_skill_v2.scripts = None

        call_count = 0

        async def mock_updater():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_skill_v1]
            return [mock_skill_v2]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        await provider._update()
        assert provider._skills["my-skill"].description == "Version 1"

        await provider._update()
        assert provider._skills["my-skill"].description == "Version 2"

    @pytest.mark.asyncio
    async def test_update_with_skills_having_scripts(self) -> None:
        """Test _update handles skills with scripts correctly."""
        mock_script = MagicMock()
        mock_skill = MagicMock()
        mock_skill.name = "scripted-skill"
        mock_skill.scripts = [mock_script]

        async def mock_updater():
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        await provider._update()

        assert "scripted-skill" in provider._skills
        assert provider._tools is not None

    @pytest.mark.asyncio
    async def test_update_creates_instructions(self) -> None:
        """Test _update recreates instructions after adding skills."""
        mock_skill = MagicMock()
        mock_skill.name = "test-skill"
        mock_skill.scripts = None

        async def mock_updater():
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        initial_instructions = provider._instructions

        await provider._update()

        # Instructions should be updated
        assert provider._instructions != initial_instructions

    @pytest.mark.asyncio
    async def test_update_creates_tools(self) -> None:
        """Test _update recreates tools after adding skills."""
        mock_skill = MagicMock()
        mock_skill.name = "test-skill"
        mock_skill.scripts = None

        async def mock_updater():
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=mock_updater)

        await provider._update()

        assert provider._tools is not None

    @pytest.mark.asyncio
    async def test_async_updater_can_perform_async_operations(self) -> None:
        """Test that skills_updater can perform async operations."""
        import asyncio

        async_counter = 0

        async def async_updater():
            nonlocal async_counter
            await asyncio.sleep(0.01)  # Simulate async operation
            async_counter += 1
            mock_skill = MagicMock()
            mock_skill.name = "async-skill"
            mock_skill.scripts = None
            return [mock_skill]

        provider = UpdatableSkillsProvider(skills_updater=async_updater)

        await provider._update()

        assert async_counter == 1
        assert "async-skill" in provider._skills

    def test_init_preserves_configuration(self) -> None:
        """Test initialization preserves all configuration options."""
        custom_template = "Custom template: {skills}"

        async def mock_updater():
            return []

        provider = UpdatableSkillsProvider(
            skills_updater=mock_updater,
            instruction_template=custom_template,
            require_script_approval=True,
            source_id="test-source",
        )

        assert provider._instruction_template == custom_template
        assert provider._require_script_approval is True
        assert provider._skills_updater is mock_updater
