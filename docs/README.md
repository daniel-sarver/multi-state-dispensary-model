# Multi-State Dispensary Model - Documentation

**Project**: Multi-State Dispensary Prediction Model (PA & FL)
**Current Phase**: Phase 3b - Model Training & Validation (Complete, ready for Phase 4)
**Last Updated**: October 23, 2025

---

## 📚 Current Documentation

### Phase 1: Data Integration (Complete ✅)

**Summary Report**:
- **[PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md)** - Complete Phase 1 summary with results
  - 741 training-eligible dispensaries achieved (98.8% of target)
  - 937 total dispensaries for competitive landscape
  - Enhanced matching algorithms with composite scoring
  - Data quality improvements and code review fixes

**Technical Documentation**:
- **[CODE_REVIEW_FIXES.md](CODE_REVIEW_FIXES.md)** - Detailed fix documentation (+98 dispensaries recovered)
  - Hemp/CBD filtering improvements
  - Address matching enhancements
  - Coordinate validation implementation
  - Testing infrastructure

**Transition Documentation**:
- **[CONTINUATION_PROMPT.md](CONTINUATION_PROMPT.md)** - Phase 1→2 transition context (now superseded by PHASE2_IMPLEMENTATION_PROMPT.md)

---

### Phase 2: Census Demographics Integration (Production Complete ✅)

**Summary Reports**:
- **[PHASE2_COMPLETION_REPORT.md](PHASE2_COMPLETION_REPORT.md)** - Production run summary & final results
  - 741/741 dispensaries with complete census data (100%)
  - 7,730 unique census tracts processed
  - 99.96% data completeness (3 tracts with standard ACS suppressions)
  - Multi-radius populations (1, 3, 5, 10, 20 miles) with area-weighting
  - 24 new census features ready for Phase 3 model training
- **[PHASE2_IMPLEMENTATION_COMPLETE.md](PHASE2_IMPLEMENTATION_COMPLETE.md)** - Implementation details & sample validation
  - All 5 modules built and tested
  - Sample validation: 20 dispensaries, 2,650 tracts, 100% success
  - Both Codex fixes applied and verified

**Architecture & Design**:
- **[PHASE2_ARCHITECTURE.md](PHASE2_ARCHITECTURE.md)** - Complete technical architecture (v1.2)
  - Census Bureau API integration strategy
  - Multi-radius population analysis (1, 3, 5, 10, 20 miles)
  - Area-weighted population calculation (prevents rural over-counting)
  - Proper CRS handling (state-specific Albers projections)
  - Secure credential management (environment variables)
  - 5 modular components with detailed specifications

**Code Review Documentation**:
- **[CODEX_REVIEW_PHASE2.md](CODEX_REVIEW_PHASE2.md)** - Critical architecture fixes
  - Area-weighted population calculation (prevents small-buffer inflation)
  - CRS transformation strategy (EPSG:3086 FL, EPSG:6565 PA)
  - API key security (environment variables, .gitignore)

**Continuation Prompts**:
- **[PHASE2_PRODUCTION_PROMPT.md](PHASE2_PRODUCTION_PROMPT.md)** - Production run prompt (741 dispensaries)

---

### Phase 3: Model Training & Validation (Complete ✅)

**Summary Reports**:
- **[PHASE3B_MODEL_TRAINING_COMPLETE.md](PHASE3B_MODEL_TRAINING_COMPLETE.md)** - Phase 3b completion report
  - Ridge regression model with R² = 0.1876 (cross-val), 0.1940 (test)
  - 2.62x improvement over baseline PA model
  - 44 engineered features with state interactions
  - Production-ready model artifact (multi_state_model_v1.pkl)

**Competitive Features**:
- **[PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md](PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md)** - Phase 3a completion report
  - 14 competitive features: multi-radius counts, saturation metrics
  - Distance-weighted competition scores
  - Demographic interaction features (affluent markets, educated urban areas)

**Code Review & Fixes**:
- **[CODEX_REVIEW_PHASE3B.md](CODEX_REVIEW_PHASE3B.md)** - Initial Codex review fixes
  - Fixed data leakage via Pipeline implementation
  - Fixed state label extraction robustness
  - Population density analysis (26% competition confounding)
- **[CODEX_REVIEW_DOUBLE_SCALING_FIX.md](CODEX_REVIEW_DOUBLE_SCALING_FIX.md)** - Critical double-scaling bug fix
  - Fixed test data being scaled twice (R² -0.1788 → 0.1940)
  - Model re-trained with correct evaluation methodology
  - All metrics validated and production-ready

**Continuation Prompts**:
- **[PHASE3B_CONTINUATION_PROMPT.md](PHASE3B_CONTINUATION_PROMPT.md)** - Model training planning document

---

## 🗂️ Archived Documentation

Located in `docs/archive/phase1/`:

- **DATA_REQUIREMENTS.md** - Initial data requirements planning
- **DATASET_ANALYSIS.md** - Early dataset analysis
- **PROCESSING_PIPELINE.md** - Initial pipeline design

These documents represent early planning and have been superseded by the completion reports.

---

## 📋 Documentation Standards

### File Naming Convention
- `PHASE[N]_[DESCRIPTION].md` - Phase-specific documentation
- `[TOPIC]_[TYPE].md` - Cross-phase documentation (e.g., CODE_REVIEW_FIXES.md)
- ALL_CAPS for primary documentation files
- lowercase for supporting files

### Documentation Types

1. **Architecture Documents**: Technical design specifications
2. **Completion Reports**: Phase summary with metrics and results
3. **Review Documents**: Code/architecture review feedback and fixes
4. **Continuation Prompts**: Context for resuming work after chat compacting

### When to Archive
- Documents superseded by completion reports
- Early planning docs after implementation complete
- Old versions of architecture after major revisions
- Keep: completion reports, final architecture, review docs

---

## 🎯 Quick Reference

### Phase 1 Status
- **Complete**: ✅ Data integration pipeline
- **Deliverables**: 741 training dispensaries, 937 total dispensaries
- **Quality**: 79.1% training coverage, 96-98 avg match confidence
- **Testing**: Comprehensive test suite implemented

### Phase 2 Status
- **Architecture**: ✅ Complete (v1.2) - production-ready
- **Implementation**: ✅ Complete - all 5 modules built and tested
- **Production Run**: ✅ Complete - 741/741 dispensaries, 7,730 tracts, 99.96% data quality
- **Deliverables**: Updated datasets with 24+ census columns, comprehensive data quality notes
- **Next Steps**: Phase 3 - Model development with enhanced census features

### Phase 3 Status
- **Phase 3a**: ✅ Complete - Competitive features engineering (14 features)
- **Phase 3b**: ✅ Complete - Model training & validation
- **Deliverables**: Ridge regression model (R² = 0.1940 test), 44 features, model artifact
- **Critical Fix**: Double-scaling bug resolved (Oct 23, 2025)
- **Next Steps**: Phase 4 - Terminal interface & production deployment

### Phase 4: Terminal Interface & Production Deployment (Complete ✅)

**Completion Reports**:
- **[PHASE4_PREDICTION_MODULE_COMPLETE.md](PHASE4_PREDICTION_MODULE_COMPLETE.md)** - Prediction module completion summary
  - MultiStatePredictor class (600+ lines)
  - State-specific confidence intervals and bootstrap implementation
  - Feature contribution analysis
  - Dynamic metric loading from training artifacts
- **[PHASE4_FEATURE_VALIDATOR_COMPLETE.md](PHASE4_FEATURE_VALIDATOR_COMPLETE.md)** - Feature validator completion summary
  - FeatureValidator class (600+ lines)
  - Auto-generation of 21 derived features (48% input reduction)
  - Range validation with training data statistics
  - 100% formula accuracy match with training pipeline
- **[PHASE4_TERMINAL_INTERFACE_COMPLETE.md](PHASE4_TERMINAL_INTERFACE_COMPLETE.md)** - Terminal interface completion summary
  - TerminalInterface class (545 lines)
  - Interactive single-site analysis with feature collection
  - Batch CSV processing with results export
  - Professional output formatting (PA model style)

**Code Implementation**:
- **[src/prediction/predictor.py](../src/prediction/predictor.py)** - Core prediction module (600+ lines)
  - `MultiStatePredictor` class with full prediction API
  - State-specific confidence intervals (FL/PA RMSE-based)
  - Bootstrap and normal approximation CI methods
  - Feature contribution analysis
  - Batch prediction capabilities
  - Comprehensive input validation
- **[src/prediction/feature_validator.py](../src/prediction/feature_validator.py)** - Feature validation and generation (600+ lines)
  - `FeatureValidator` class for input validation
  - Auto-generates 21 derived features from 23 base inputs
  - Range validation using training data statistics
  - Formula accuracy: 100% match with training pipeline
  - Batch processing capabilities
- **[src/terminal/cli.py](../src/terminal/cli.py)** - Terminal interface (545 lines)
  - `TerminalInterface` class for interactive predictions
  - Single-site analysis mode with guided input
  - Batch CSV processing mode
  - Model information display
  - Professional results formatting with visual hierarchy

**Codex Reviews**:
- **Predictor Module Review** (Oct 23, 2025) - All findings resolved
  - Dynamic RMSE loading from training_report ✅
  - Bootstrap CI implementation ✅
  - State indicator validation guards ✅
  - Removed unused imports ✅
- **Feature Validator Review** (Oct 23, 2025) - All findings resolved
  - Fixed affluent_market_5mi formula (10,000× scaling error) ✅
  - Fixed educated_urban_score formula (1,000× scaling error) ✅
  - Fixed age_adjusted_catchment_3mi formula (wrong calculation) ✅
  - competition_weighted_20mi now required as input (distance matrix needed) ✅

**Status**: Core prediction, validation, and terminal interface complete - production ready

---

### Phase 5: Model Improvement - Exploration (Complete ✅)

**Completion Reports**:
- **[PHASE5_EXPLORATION_COMPLETE.md](PHASE5_EXPLORATION_COMPLETE.md)** - Phase 5 exploration summary
  - Data exploration and improvement opportunity analysis
  - Temporal adjustments analysis (not needed - 99% of sites mature)
  - Outlier detection and review (4 sites analyzed, all kept as legitimate)
  - Placer correction methodology designed (8 Insa stores for calibration)
  - Decision rationale and expected impact analysis
- **[PHASE5_DATA_EXPLORATION_FINDINGS.md](PHASE5_DATA_EXPLORATION_FINDINGS.md)** - Detailed exploration findings
  - Visit distribution statistics by state
  - Top/bottom performer analysis
  - Revised implementation strategy
- **[OUTLIER_REVIEW_DECISION.md](OUTLIER_REVIEW_DECISION.md)** - Outlier review decisions
  - Detailed review of 4 low-traffic FL sites
  - Decision to keep all (legitimate market dynamics)
  - Documentation precedent for future reviews

**Code Implementation**:
- **[src/modeling/detect_outliers.py](../src/modeling/detect_outliers.py)** - Outlier detection script (353 lines)
  - Multi-method detection (statistical, business logic, residual-based)
  - Automated flagging and recommendations
  - CSV export for manual review
- **[src/modeling/placer_correction.py](../src/modeling/placer_correction.py)** - Placer calibration script (412 lines)
  - Ready-to-run correction using Insa actual data
  - Multiple correction methods (simple, state-specific, size-adjusted)
  - Automated dataset generation
  - **Status**: Awaiting Insa actual visit data

**Key Findings**:
- ❌ Temporal adjustments not needed (only 1 of 741 sites < 12 months old)
- ❌ Outlier removal not recommended (all 4 low-traffic sites are legitimate)
- ✅ **Placer correction is highest-impact opportunity** (+0.03 to +0.08 R²)

**Status**: Exploration complete - Ready for Placer calibration (pending Insa actual data)

**Next Steps**:
- **Placer Calibration** (Priority 1) - Obtain Insa actual monthly visits for 8 FL stores
  - Expected improvement: +0.03 to +0.08 R²
  - Script ready to run once data provided
- Brand effects analysis (Priority 2)
- Digital footprint features (Priority 3)

---

## 📖 Reading Order for New Contributors

1. **Start Here**: [CLAUDE.md](../CLAUDE.md) - Project guidelines and principles
2. **Executive Summary**: [MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md](MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md) - **For business stakeholders** - Model capabilities, limitations, and appropriate use cases
3. **Current Work**: [PHASE5_EXPLORATION_COMPLETE.md](PHASE5_EXPLORATION_COMPLETE.md) - **Model improvement exploration** - Data analysis, outlier review, Placer correction design
4. **Improvement Roadmap**: [MODEL_IMPROVEMENT_IDEAS.md](MODEL_IMPROVEMENT_IDEAS.md) - **Full strategy** - Temporal, outliers, Placer, brand, digital footprint
5. **Phase 1**: [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md) - Data integration results
6. **Phase 2**: [PHASE2_COMPLETION_REPORT.md](PHASE2_COMPLETION_REPORT.md) - Census demographics integration
7. **Phase 3**: [PHASE3B_MODEL_TRAINING_COMPLETE.md](PHASE3B_MODEL_TRAINING_COMPLETE.md) - Model training & validation
8. **Phase 4**: [PHASE4_TERMINAL_INTERFACE_COMPLETE.md](PHASE4_TERMINAL_INTERFACE_COMPLETE.md) - Terminal interface & production deployment
9. **Code Reviews**: [CODEX_REVIEW_DOUBLE_SCALING_FIX.md](CODEX_REVIEW_DOUBLE_SCALING_FIX.md) - Critical bug fix (read this!)
10. **Technical**: [PHASE2_ARCHITECTURE.md](PHASE2_ARCHITECTURE.md) - Census integration architecture

---

## 🔄 Document Update Log

| Date | Document | Change |
|------|----------|--------|
| 2025-10-24 | PHASE5_EXPLORATION_COMPLETE.md | Created - Phase 5 exploration summary (temporal, outliers, Placer correction) |
| 2025-10-24 | PHASE5_DATA_EXPLORATION_FINDINGS.md | Created - Detailed data exploration findings and statistics |
| 2025-10-24 | OUTLIER_REVIEW_DECISION.md | Created - Outlier review decisions and rationale (keep all 4 sites) |
| 2025-10-24 | src/modeling/detect_outliers.py | Created - Outlier detection script (353 lines, multi-method detection) |
| 2025-10-24 | src/modeling/placer_correction.py | Created - Placer calibration script (412 lines, ready for Insa data) |
| 2025-10-24 | MODEL_IMPROVEMENT_IDEAS.md | Updated - Added outlier removal and Placer correction priorities |
| 2025-10-24 | README.md | Updated - Added Phase 5 status and updated key documents |
| 2025-10-24 | docs/README.md | Updated - Added Phase 5 section with complete documentation |
| 2025-10-23 | MODEL_IMPROVEMENT_IDEAS.md | Created - Comprehensive roadmap to improve R² from 0.19 to 0.30+ |
| 2025-10-23 | CONTINUATION_PROMPT_MODEL_IMPROVEMENT.md | Created - Quick-start prompt for next session (model improvement phase) |
| 2025-10-23 | README.md | Updated - Added model improvement roadmap to key documents |
| 2025-10-23 | docs/README.md | Updated - Added model improvement to next steps and reading order |
| 2025-10-23 | MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md | Created - Executive summary for business stakeholders (model capabilities, limitations, use cases) |
| 2025-10-23 | src/prediction/predictor.py | Fixed - Eliminated sklearn warnings by wrapping arrays in DataFrames with feature names |
| 2025-10-23 | docs/README.md | Updated - Added executive summary to reading order |
| 2025-10-23 | PHASE4_TERMINAL_INTERFACE_COMPLETE.md | Created - Terminal interface completion report (545 lines) |
| 2025-10-23 | src/terminal/cli.py | Created - Interactive terminal interface with single-site and batch modes |
| 2025-10-23 | test_cli.py | Created - CLI test suite with comprehensive testing |
| 2025-10-23 | data/examples/batch_example.csv | Created - Sample batch input file for testing |
| 2025-10-23 | README.md | Updated - Added terminal interface to Phase 4 progress |
| 2025-10-23 | docs/README.md | Updated - Added terminal interface documentation and status |
| 2025-10-23 | PHASE4_FEATURE_VALIDATOR_COMPLETE.md | Created - Feature validator completion report with Codex fixes |
| 2025-10-23 | src/prediction/feature_validator.py | Created - Feature validation and auto-generation module (600+ lines) |
| 2025-10-23 | data/models/feature_ranges.json | Created - Training data statistics for validation |
| 2025-10-23 | README.md | Updated - Added feature validator to Phase 4 progress |
| 2025-10-23 | docs/README.md | Updated - Added feature validator documentation and Codex review |
| 2025-10-23 | src/prediction/predictor.py | Created - Core prediction module with MultiStatePredictor class (600+ lines) |
| 2025-10-23 | README.md | Updated - Added Phase 4 progress section with prediction module details |
| 2025-10-23 | docs/README.md | Updated - Added Phase 4 section documenting predictor module and Codex reviews |
| 2025-10-23 | CODEX_REVIEW_DOUBLE_SCALING_FIX.md | Created - critical double-scaling bug fix documentation (R² -0.1788 → 0.1940) |
| 2025-10-23 | PHASE3B_MODEL_TRAINING_COMPLETE.md | Updated - added note about double-scaling fix and corrected metrics |
| 2025-10-23 | README.md | Updated - added Phase 3 status and double-scaling fix reference |
| 2025-10-23 | docs/README.md | Updated - added Phase 3 section and double-scaling fix |
| 2025-10-23 | PHASE3B_MODEL_TRAINING_COMPLETE.md | Created - Phase 3b completion report |
| 2025-10-23 | PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md | Created - Phase 3a completion report |
| 2025-10-23 | CODEX_REVIEW_PHASE3B.md | Created - Codex review fixes (data leakage, state labels, population analysis) |
| 2025-10-23 | PHASE2_COMPLETION_REPORT.md | Created - comprehensive production run summary with final results |
| 2025-10-23 | PHASE2_DATA_QUALITY_NOTES.md | Created - documents incomplete tracts, ACS suppressions, downstream compatibility |
| 2025-10-23 | README.md | Updated Phase 2 status to reflect production completion |
| 2025-10-23 | docs/README.md | Added PHASE2_COMPLETION_REPORT.md to documentation index |
| 2025-10-22 | PHASE2_IMPLEMENTATION_COMPLETE.md | Created - implementation summary & sample results |
| 2025-10-22 | PHASE2_PRODUCTION_PROMPT.md | Created - continuation prompt for production run |
| 2025-10-22 | PHASE2_ARCHITECTURE.md | v1.2 - Codex review fixes (area-weighting, CRS, credentials) |
| 2025-10-22 | CODEX_REVIEW_PHASE2.md | Created - documents critical architecture fixes |
| 2025-10-22 | archive/phase1/ | Archived early planning documents |
| 2025-10-22 | CODE_REVIEW_FIXES.md | Updated with final Phase 1 statistics |
| 2025-10-22 | PHASE1_COMPLETION_REPORT.md | Updated with code review improvements |

---

*For questions about documentation, refer to the project guidelines in [CLAUDE.md](../CLAUDE.md)*
