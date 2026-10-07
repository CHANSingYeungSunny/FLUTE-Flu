# One-time final Test — authorization request

A lawful champion **nlinear** is frozen from the explicit 160-cell Stage-F cohort.

Bindings:

- champion run ids: 40 (see frozen_model_manifest.json)
- Stage F cohort manifest sha256: `8695b8ea6151c5dd350411449141e4e547c7bd0aaa263e402695279477e0327d`
- frozen_model_manifest sha256: `558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5`
- authoritative plan sha256: `aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961`
- source aggregate sha256: `47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4`

To authorize, set `ONE_TIME_TEST_AUTHORIZATION=<token>` (see the command) and run
`results/innovation/test_readiness/one_time_test_command.sh`. The command refuses
unless the token is present AND the frozen manifest hash matches.

Test remains SEALED until then.