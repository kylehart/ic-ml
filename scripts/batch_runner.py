#!/usr/bin/env python3
"""
Batch Runner for IC-ML Project
Run multiple experiments and generate consolidated reports
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class BatchRunner:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def run_command(self, cmd: str, description: str) -> Dict[str, Any]:
        """Execute a command and capture results"""
        print(f"\n🔄 {description}")
        print(f"   Command: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0
            print(f"   {'✅' if success else '❌'} {'Completed' if success else 'Failed'}")

            return {
                "description": description,
                "command": cmd,
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout exceeded")
            return {
                "description": description,
                "command": cmd,
                "success": False,
                "error": "Timeout exceeded",
                "timestamp": datetime.now().isoformat()
            }

    def run_health_quiz_batch(self):
        """Run health quiz for all personas"""
        personas = [
            "Sarah Chen",
            "Marcus Rodriguez",
            "Lisa Thompson"
        ]

        for persona in personas:
            cmd = f'python3 src/run_health_quiz.py --persona "{persona}" --model gpt4o_mini'
            result = self.run_command(cmd, f"Health Quiz: {persona}")
            self.results.append(result)

    def run_classification_tests(self):
        """Run product classification tests"""
        test_products = [
            "Echinacea Immune Support",
            "Stress Relief Complex",
            "Joint Support Formula"
        ]

        for product in test_products:
            cmd = f'python3 src/run_assign_cat.py --single-product "{product}" --model gpt4o_mini'
            result = self.run_command(cmd, f"Classification: {product}")
            self.results.append(result)

    def generate_summary(self):
        """Generate summary report"""
        duration = (datetime.now() - self.start_time).total_seconds()

        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful

        summary = {
            "run_date": self.start_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": len(self.results),
            "successful": successful,
            "failed": failed,
            "results": self.results
        }

        # Save JSON report
        report_path = Path(f"batch_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n📊 Batch Run Summary")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Total: {len(self.results)}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📄 Report: {report_path}")

        return summary

def main():
    """Main batch runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 scripts/batch_runner.py [--quiz|--classify|--all]")
        print("  --quiz     Run all health quiz personas")
        print("  --classify Run classification tests")
        print("  --all      Run everything (default)")
        return

    runner = BatchRunner()

    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"

    print("🚀 Starting IC-ML Batch Runner")
    print(f"   Mode: {mode}")

    if mode in ["--quiz", "--all"]:
        runner.run_health_quiz_batch()

    if mode in ["--classify", "--all"]:
        runner.run_classification_tests()

    runner.generate_summary()

if __name__ == "__main__":
    main()