// Minimal Circom circuit: checks confidence >= threshold (scaled by 1000)
pragma circom 2.1.6;

template ConfidenceThreshold() {
    signal input confidence;     // integer confidence * 1000
    signal input threshold;      // integer threshold * 1000
    signal output ok;

    ok <== confidence >= threshold;
}

component main = ConfidenceThreshold();


