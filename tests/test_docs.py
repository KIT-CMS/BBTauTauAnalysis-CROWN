"""Doc-check tests (Task 23): keep the SM/NMSSM documentation honest.

Two independent checks:

1. The retired analysis identity `xyh_bbtautau` (see
   `tests/test_run2_v15_configuration.py` for the code-level version of this
   check) must never appear inside a fenced (```` ``` ````) code block of any
   doc file -- a copy-pasted command containing it would simply fail today
   (the real identity is `bbtautau`). Prose explaining the historical rename
   is fine and is intentionally NOT checked -- only fenced code blocks are
   parsed.
2. `docs/sm_2018_efficiency_workflow.md` carries the copyable command blocks
   the SM 2018 UParT b-tag-efficiency chain is built from (spec
   "Build Interface"): the committed KingMaker sample list, `ProduceNtuples`,
   TauFakeFactors preselection, the calculation step, and the
   payload install step.

`docs/` is untracked/user-local in this repo (see .gitignore) and is therefore
absent on a fresh clone, so both doc checks skip when it is not there -- the
same treatment CLAUDE.md already gets below. README.md is tracked and is always
checked.
"""
import re
import unittest
from pathlib import Path

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
README = ANALYSIS_ROOT / "README.md"
DOCS_DIR = ANALYSIS_ROOT / "docs"
CLAUDE_MD = ANALYSIS_ROOT / "CLAUDE.md"
WORKFLOW_DOC = DOCS_DIR / "sm_2018_efficiency_workflow.md"

# The retired analysis identity. Checked as the bare token (a superset of the
# more specific "-DANALYSIS=xyh_bbtautau" the spec calls out): no legitimate
# copyable command in this repo needs to spell "xyh_bbtautau" at all any
# more, quoted or not, so forbidding the bare token in code blocks cannot
# produce a false positive against real content.
FORBIDDEN_IDENTITY_TOKEN = "xyh_bbtautau"

# Matches ``` ... ``` fenced blocks (any/no language tag), non-greedy so
# adjacent blocks in the same file are not merged into one match.
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)


def _code_blocks(text):
    """Return the contents of every fenced code block in *text*."""
    return _FENCE_RE.findall(text)


class ForbiddenAnalysisIdentityInCodeBlocksTest(unittest.TestCase):
    """`xyh_bbtautau` (e.g. as `-DANALYSIS=xyh_bbtautau`) must not appear in
    any fenced code block of README.md, docs/*.md, or CLAUDE.md (if present).
    """

    def _assert_no_forbidden_token_in_code(self, path: Path):
        text = path.read_text()
        for block in _code_blocks(text):
            self.assertNotIn(
                FORBIDDEN_IDENTITY_TOKEN,
                block,
                f"{path} contains a fenced code block referencing the "
                f"retired '{FORBIDDEN_IDENTITY_TOKEN}' analysis identity; "
                f"active command examples must use 'bbtautau'.",
            )

    def test_readme_has_no_forbidden_identity_in_code_blocks(self):
        self.assertTrue(README.is_file(), f"{README} not found")
        self._assert_no_forbidden_token_in_code(README)

    def test_docs_have_no_forbidden_identity_in_code_blocks(self):
        doc_files = sorted(DOCS_DIR.glob("*.md")) if DOCS_DIR.is_dir() else []
        if not doc_files:
            self.skipTest(f"{DOCS_DIR} is untracked/local-only and absent here")
        for path in doc_files:
            self._assert_no_forbidden_token_in_code(path)

    def test_claude_md_has_no_forbidden_identity_in_code_blocks_if_present(self):
        # CLAUDE.md is untracked/user-local in this repo (see .gitignore) and
        # is therefore absent on a fresh clone or CI checkout -- only check
        # it when it actually exists.
        if not CLAUDE_MD.is_file():
            self.skipTest(f"{CLAUDE_MD} is untracked/local-only and absent here")
        self._assert_no_forbidden_token_in_code(CLAUDE_MD)


class Sm2018EfficiencyWorkflowDocTest(unittest.TestCase):
    """`docs/sm_2018_efficiency_workflow.md` carries the copyable command
    blocks the SM 2018 UParT b-tag-efficiency chain is built from -- five
    steps in six blocks (Step 2 carries a local-build alternative next to the
    `ProduceNtuples` submission)."""

    # One required token per step, in step order; each must be found inside
    # at least one fenced code block of the workflow doc.
    REQUIRED_STEP_TOKENS = [
        ("committed KingMaker sample lists", "sm_2018_inclusive.txt"),
        ("n-tuple production", "ProduceNtuples"),
        ("TauFakeFactors preselection", "preselection.py"),
        ("b-tag efficiency calculation", "btag_efficiency.py"),
        ("payload install target", "upart/2018"),
    ]

    @classmethod
    def setUpClass(cls):
        if not WORKFLOW_DOC.is_file():
            raise unittest.SkipTest(
                f"{WORKFLOW_DOC} is untracked/local-only and absent here"
            )
        cls.doc_exists = True
        cls.blocks = _code_blocks(WORKFLOW_DOC.read_text())

    def test_workflow_doc_exists(self):
        self.assertTrue(self.doc_exists, f"{WORKFLOW_DOC} not found")

    def test_at_least_six_command_blocks_present(self):
        self.assertGreaterEqual(
            len(self.blocks),
            6,
            f"expected at least 6 fenced code blocks in {WORKFLOW_DOC}, "
            f"found {len(self.blocks)}",
        )

    def test_each_workflow_step_has_a_dedicated_command_block(self):
        """Each of the five required steps must have its token in a distinct block.

        This prevents stale/deleted step blocks from going unnoticed: if Step 2's
        block contained Step 1's token, then deleting Step 1's block would not be
        caught by a simple "token in at least one block" check. By tracking the
        FIRST block index where each token appears, we ensure each step owns its
        own dedicated block."""
        first_match_indices = {}
        for step_name, token in self.REQUIRED_STEP_TOKENS:
            for idx, block in enumerate(self.blocks):
                if token in block:
                    first_match_indices[token] = idx
                    break
            self.assertIn(
                token,
                first_match_indices,
                f"no fenced code block in {WORKFLOW_DOC} contains '{token}' "
                f"(step: {step_name})",
            )

        # Verify the six tokens have distinct FIRST-match block indices.
        distinct_indices = set(first_match_indices.values())
        self.assertEqual(
            len(distinct_indices),
            len(self.REQUIRED_STEP_TOKENS),
            f"Expected each of the {len(self.REQUIRED_STEP_TOKENS)} workflow steps "
            f"to have its token in a distinct block, but first-match indices are "
            f"not all unique: {first_match_indices}. Each step must keep its own "
            f"dedicated command block.",
        )


if __name__ == "__main__":
    unittest.main()
