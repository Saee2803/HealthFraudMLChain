"""
routes/admin_routes.py

Admin endpoints for approving, committing to blockchain, and running verification.
Register blueprint in main app to enable routes.
"""
from flask import Blueprint, request, jsonify
from services.rules_engine import apply_transition, RuleViolation
from services.blockchain_service import commit_block, verify_chain

bp = Blueprint('admin_routes', __name__)


@bp.route('/claims/<claim_id>/admin_approve', methods=['PUT'])
def admin_approve(claim_id):
    actor = request.environ.get('actor') or {'id': 'admin-1', 'role': 'admin'}
    try:
        new_state = apply_transition(actor, 'admin_approve', claim_id, details={'note': request.json.get('note')})
        return jsonify({'claim_id': claim_id, 'new_state': new_state}), 200
    except RuleViolation as rv:
        return jsonify({'error': str(rv)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/claims/<claim_id>/commit', methods=['POST'])
def commit(claim_id):
    actor = request.environ.get('actor') or {'id': 'admin-1', 'role': 'admin'}
    signer_priv_pem = None
    signer_key_id = request.json.get('signer_key_id')
    # In production, signer_priv_pem must be retrieved from KMS/HSM
    try:
        block = commit_block(claim_id, actor, signer_priv_pem=signer_priv_pem, signer_key_id=signer_key_id)
        return jsonify({'block_hash': block['block_hash']}), 200
    except PermissionError as pe:
        return jsonify({'error': str(pe)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/blockchain/verify', methods=['POST'])
def run_verify():
    report = verify_chain()
    return jsonify(report), 200
