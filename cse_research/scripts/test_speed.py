import time
from cse.features.pipeline import PhaseDataManager
from cse.models.deep.architectures import build_deep_model, MODEL_REGISTRY
from cse.models.deep.trainer import DeepSequenceTrainer

mgr = PhaseDataManager()
seq_data = mgr.get_sequence_windows('P1', horizon=1, feature_set='C', lookback=20)
print('Data shapes: train', seq_data.train.X_seq.shape, 'inner_val', seq_data.inner_val.X_seq.shape)

for m_type in list(MODEL_REGISTRY.keys()):
    m = build_deep_model(m_type, in_features=seq_data.train.X_seq.shape[2], lookback=20)
    params = m.count_parameters()
    t0 = time.time()
    trainer = DeepSequenceTrainer(m, max_epochs=5, patience=2, seed=42)
    res = trainer.fit(seq_data.train, seq_data.inner_val, batch_size=128)
    dt = time.time() - t0
    ep = res["total_epochs"]
    print(f"{m_type:15s}: {params:6d} params, {ep} epochs, {dt:.2f}s ({dt/ep:.3f}s/ep)")
