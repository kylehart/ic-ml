# IC-ML Tasks and Automation

## Immediate Tasks
- [ ] Clean up slug-related files
  ```bash
  rm add_slugs_to_catalog.py
  rm test_slug_generation.py
  rm test_real_urls.py
  rm verify_slugs.py
  rm debug_raw_response_0.txt
  ```

## Pre-Commit Checklist
- [ ] Run health quiz test: `python3 src/run_health_quiz.py --persona "Sarah Chen" --model gpt4o_mini`
- [ ] Run classification test: `python3 src/run_assign_cat.py --single-product "Test Product" --model gpt4o_mini`
- [ ] Check cost tracking: `ls -la runs/*/outputs/client_cost_breakdown.json`

## Nightly Batch Jobs
```bash
# Full test suite
python3 src/run_health_quiz.py --all-personas --model gpt4o_mini
python3 src/run_assign_cat.py --input data/rogue-herbalist/minimal-product-catalog.csv --sample 50

# Generate reports
python3 scripts/generate_daily_report.py
```

## Future Enhancements
- [ ] Implement web service deployment
- [ ] Add more health quiz personas
- [ ] Create cost optimization analysis tool
- [ ] Build automated testing framework

## Automation Scripts Needed
- [ ] `scripts/nightly_batch.py` - Orchestrate overnight runs
- [ ] `scripts/consolidate_reports.py` - Merge multiple run outputs
- [ ] `scripts/cost_analyzer.py` - Track spending trends
- [ ] `scripts/test_suite.py` - Comprehensive testing

## Documentation Tasks
- [ ] Update README with current capabilities
- [ ] Create API documentation for web service
- [ ] Document cost optimization strategies