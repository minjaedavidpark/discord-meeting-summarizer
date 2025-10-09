# Contributing to Discord Meeting Summarizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🐛 Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant log output

## 💡 Suggesting Features

Feature suggestions are welcome! Please:
- Check existing issues first to avoid duplicates
- Clearly describe the feature and its benefits
- Explain any implementation ideas you have

## 🔧 Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/minjaedavidpark/discord-meeting-summarizer.git
   cd discord-meeting-summarizer
   ```

2. **Set up development environment**
   ```bash
   ./setup.sh
   source venv/bin/activate
   ```

3. **Configure for testing**
   ```bash
   cp .env.example .env
   # Add your test credentials
   ```

4. **Run tests**
   ```bash
   python scripts/test_config.py
   ```

## 📝 Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to functions and classes
- Keep functions focused and modular
- Add comments for complex logic

## 🔀 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Test your changes thoroughly
   - Update documentation if needed

3. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: brief description"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub

5. **PR Description**
   Include:
   - What changes were made
   - Why they were made
   - How to test them
   - Any breaking changes

## 🎯 Priority Areas

Areas where contributions are especially welcome:

- **Speaker Diarization**: Identify who is speaking
- **Multi-language Support**: Support for languages beyond English
- **Better Audio Processing**: Improved mixing and quality
- **File Size Optimization**: Handle large meetings better
- **UI/Dashboard**: Web interface for viewing summaries
- **Integrations**: Slack, Notion, Trello, etc.
- **Tests**: Unit and integration tests
- **Documentation**: Improve setup guides and examples

## 🧪 Testing

Before submitting:
- Test with actual Discord voice channels
- Verify transcription works correctly
- Check summary quality
- Test Docker deployment if modifying Dockerfile
- Run the test config script

## 📚 Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Python Best Practices](https://docs.python-guide.org/)

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards others

## 💬 Questions?

Feel free to:
- Open an issue for discussion
- Ask in pull request comments
- Reach out to maintainers

Thank you for contributing! 🎉

