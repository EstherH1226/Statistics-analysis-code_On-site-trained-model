"""Compatibility entry point: the revised manuscript uses GEE, not McNemar.
The historical any-observer-positive analysis is available in Git history.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gee_analysis_package"))
from gee_acceptance_analysis import main
if __name__ == "__main__":
    print("The revised analysis uses patient-clustered GEE; no McNemar test is run.", file=sys.stderr)
    main()
