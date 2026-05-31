# cosign is used to sign and verify container images.
# See: https://docs.sigstore.dev/cosign/overview/
#
# Typical usage (run after docker push):
#
#   cosign sign \
#     --key cosign.key \
#     <registry>/<image>@<digest>
#
#   cosign verify \
#     --key cosign.pub \
#     <registry>/<image>@<digest>
#
# Key generation (one-time, store cosign.key in a secret manager):
#
#   cosign generate-key-pair
#
# The public key (cosign.pub) can be committed to this repo.
# NEVER commit cosign.key.

# Placeholder — add cosign.pub here after key generation.
