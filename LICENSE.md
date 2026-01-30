# Remind License

## Overview

**Remind** is open-source software with a dual-licensing model:

- **Open Source**: The core software is licensed under the **GNU Affero General Public License v3 (AGPL v3)**
- **Premium Features**: Advanced functionality requires a commercial license
- **Commercial Use**: Business and production deployments require a license

---

## GNU Affero General Public License v3 (AGPL v3)

The core Remind software is free software distributed under the AGPL v3 license. You are free to:

✅ **Use** — Run Remind for personal or non-commercial purposes
✅ **Modify** — Fork and customize the software
✅ **Distribute** — Share your modified versions

**With one condition:** If you modify Remind and distribute it (including running it as a service), you must:

- Publish your source code modifications
- License your changes under AGPL v3
- Make source available to users of your modified version

See [GNU AGPL v3 Full Text](https://www.gnu.org/licenses/agpl-3.0.html) for details.

---

## Premium Features

The following features require an active **Remind Premium License**:

- 🤖 AI-powered reminder rephrasing (OpenAI integration)
- 📬 Smart nudge escalation (configurable re-notifications)
- 🔐 Priority support

**Free features:**
- Core reminder creation and scheduling
- Desktop notifications
- Local database storage
- CLI interface
- Custom timezone support

---

## Commercial License

A **Commercial License** is required for:

1. **Business Use** — Using Remind in a commercial capacity (for-profit organizations)
2. **Production Deployments** — Running Remind as part of a SaaS or managed service
3. **Proprietary Software** — Distributing Remind as part of closed-source software
4. **License Exceptions** — Using premium features without sharing modifications

### How to Get a License

```bash
remind license --purchase
```

Or visit: [remind.sh/license](https://remind.sh/license)

**License Terms:**
- One-time purchase (perpetual license)
- No expiration or renewal fees
- Covers all updates within major version
- Includes email support

---

## Personal & Non-Commercial Use

Non-commercial users can:

- Run Remind for personal task management
- Modify the code for personal use (modifications not shared with others)
- Deploy on personal servers or local machines
- Use free features indefinitely

**No license required for non-commercial use.**

---

## Educational & Research Use

Educators and researchers can use Remind for teaching and research at **no cost**. Request an academic license:

```bash
remind license --academic
```

Includes all premium features.

---

## Enforcement

We use local license validation (no phone home). Your license token is checked locally via `~/.remind/license.json`.

**Premium features will not function without a valid license token.** The software continues to work with free features.

---

## Intellectual Property

- **Trademarks**: "Remind" is a registered trademark of [Your Company]. Do not use "Remind" in derivative products without permission.
- **Documentation**: Licensed separately under Creative Commons Attribution 4.0 (CC-BY-4.0)
- **Third-Party Dependencies**: See `DEPENDENCIES.md` for licenses of included libraries

---

## Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OR DISTRIBUTION OF THIS SOFTWARE.

---

## Questions?

- **License inquiries**: [license@remind.sh](mailto:license@remind.sh)
- **Technical support**: [support@remind.sh](mailto:support@remind.sh)
- **Report abuse**: [abuse@remind.sh](mailto:abuse@remind.sh)

---

**Last Updated**: 2025-01-30
**Version**: 1.0
