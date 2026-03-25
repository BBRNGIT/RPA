/**
 * RPA Neural LLM - JavaScript Inference Engine
 *
 * Real transformer inference running in the browser!
 * Character-level tokenization (NO word-piece)
 *
 * Features:
 * - Multi-head self-attention
 * - Layer normalization
 * - Temperature sampling
 * - Top-K filtering
 */

class NeuralLLM {
    constructor() {
        this.model = null;
        this.tokenizer = null;
        this.ready = false;
    }

    async loadModel(url) {
        console.log('Loading model from:', url);

        try {
            const response = await fetch(url);
            const data = await response.json();

            this.model = {
                config: data.config,
                embedding: {
                    weight: this.toArray(data.embedding.weight),
                    pos_weight: this.toArray(data.embedding.pos_weight),
                },
                blocks: data.blocks.map(b => ({
                    attention: {
                        W_q: this.toArray(b.attention.W_q),
                        W_k: this.toArray(b.attention.W_k),
                        W_v: this.toArray(b.attention.W_v),
                        W_o: this.toArray(b.attention.W_o),
                    },
                    ffn: {
                        W1: this.toArray(b.ffn.W1),
                        W2: this.toArray(b.ffn.W2),
                    },
                    ln1: {
                        gamma: this.toArray(b.ln1.gamma),
                        beta: this.toArray(b.ln1.beta),
                    },
                    ln2: {
                        gamma: this.toArray(b.ln2.gamma),
                        beta: this.toArray(b.ln2.beta),
                    }
                })),
                ln_f: {
                    gamma: this.toArray(data.ln_f.gamma),
                    beta: this.toArray(data.ln_f.beta),
                }
            };

            this.tokenizer = {
                chars: data.tokenizer.chars,
                vocab_size: data.tokenizer.vocab_size,
            };

            this.ready = true;
            console.log('Model loaded! Parameters:', this.countParams());
            return true;
        } catch (error) {
            console.error('Failed to load model:', error);
            return false;
        }
    }

    toArray(nestedArray) {
        if (typeof nestedArray[0] === 'number') {
            return new Float32Array(nestedArray);
        }
        return nestedArray.map(row => new Float32Array(row));
    }

    countParams() {
        let count = 0;
        count += this.model.embedding.weight.length * this.model.embedding.weight[0].length;
        count += this.model.embedding.pos_weight.length * this.model.embedding.pos_weight[0].length;

        for (const block of this.model.blocks) {
            count += block.attention.W_q.length * block.attention.W_q[0].length;
            count += block.attention.W_k.length * block.attention.W_k[0].length;
            count += block.attention.W_v.length * block.attention.W_v[0].length;
            count += block.attention.W_o.length * block.attention.W_o[0].length;
            count += block.ffn.W1.length * block.ffn.W1[0].length;
            count += block.ffn.W2.length * block.ffn.W2[0].length;
        }

        return count;
    }

    encode(text) {
        const ids = [];
        for (const c of text) {
            const idx = this.tokenizer.chars.indexOf(c);
            ids.push(idx >= 0 ? idx : this.tokenizer.vocab_size - 1);
        }
        return ids;
    }

    decode(ids) {
        const chars = [];
        for (const id of ids) {
            if (id >= 0 && id < this.tokenizer.chars.length) {
                chars.push(this.tokenizer.chars[id]);
            }
        }
        return chars.join('');
    }

    // Matrix operations
    matmul(a, b) {
        const m = a.length;
        const k = a[0].length;
        const n = b[0].length;

        const result = new Array(m);
        for (let i = 0; i < m; i++) {
            result[i] = new Float32Array(n);
            for (let j = 0; j < n; j++) {
                let sum = 0;
                for (let l = 0; l < k; l++) {
                    sum += a[i][l] * b[l][j];
                }
                result[i][j] = sum;
            }
        }
        return result;
    }

    layerNorm(x, gamma, beta) {
        const eps = 1e-5;
        const seqLen = x.length;
        const dModel = x[0].length;

        const result = new Array(seqLen);

        for (let i = 0; i < seqLen; i++) {
            let mean = 0;
            for (let j = 0; j < dModel; j++) {
                mean += x[i][j];
            }
            mean /= dModel;

            let variance = 0;
            for (let j = 0; j < dModel; j++) {
                variance += (x[i][j] - mean) ** 2;
            }
            variance /= dModel;

            const std = Math.sqrt(variance + eps);

            result[i] = new Float32Array(dModel);
            for (let j = 0; j < dModel; j++) {
                result[i][j] = gamma[j] * (x[i][j] - mean) / std + beta[j];
            }
        }

        return result;
    }

    softmax(x) {
        const max = Math.max(...x);
        const exp = x.map(v => Math.exp(v - max));
        const sum = exp.reduce((a, b) => a + b, 0);
        return exp.map(v => v / sum);
    }

    attention(x, block) {
        const seqLen = x.length;
        const dModel = x[0].length;
        const numHeads = this.model.config.num_heads;
        const headDim = dModel / numHeads;

        const Q = this.matmul(x, block.attention.W_q);
        const K = this.matmul(x, block.attention.W_k);
        const V = this.matmul(x, block.attention.W_v);

        const output = new Array(seqLen);
        for (let i = 0; i < seqLen; i++) {
            output[i] = new Float32Array(dModel);
        }

        for (let h = 0; h < numHeads; h++) {
            const start = h * headDim;
            const end = start + headDim;

            const headQ = Q.map(row => row.slice(start, end));
            const headK = K.map(row => row.slice(start, end));
            const headV = V.map(row => row.slice(start, end));

            const scale = 1 / Math.sqrt(headDim);
            const scores = new Array(seqLen);

            for (let i = 0; i < seqLen; i++) {
                scores[i] = new Float32Array(seqLen);
                for (let j = 0; j < seqLen; j++) {
                    if (j > i) {
                        scores[i][j] = -1e9;
                    } else {
                        let dot = 0;
                        for (let k = 0; k < headDim; k++) {
                            dot += headQ[i][k] * headK[j][k];
                        }
                        scores[i][j] = dot * scale;
                    }
                }
            }

            const attnOut = new Array(seqLen);
            for (let i = 0; i < seqLen; i++) {
                const probs = this.softmax(Array.from(scores[i]));
                attnOut[i] = new Float32Array(headDim);

                for (let j = 0; j < seqLen; j++) {
                    for (let k = 0; k < headDim; k++) {
                        attnOut[i][k] += probs[j] * headV[j][k];
                    }
                }

                for (let k = 0; k < headDim; k++) {
                    output[i][start + k] = attnOut[i][k];
                }
            }
        }

        return this.matmul(output, block.attention.W_o);
    }

    feedForward(x, block) {
        const hidden = this.matmul(x, block.ffn.W1);

        for (let i = 0; i < hidden.length; i++) {
            for (let j = 0; j < hidden[i].length; j++) {
                hidden[i][j] = Math.max(0, hidden[i][j]);
            }
        }

        return this.matmul(hidden, block.ffn.W2);
    }

    forward(tokenIds) {
        const seqLen = tokenIds.length;
        const dModel = this.model.config.d_model;

        const x = new Array(seqLen);
        for (let i = 0; i < seqLen; i++) {
            x[i] = new Float32Array(dModel);
            for (let j = 0; j < dModel; j++) {
                x[i][j] = this.model.embedding.weight[tokenIds[i]][j];
                if (i < this.model.embedding.pos_weight.length) {
                    x[i][j] += this.model.embedding.pos_weight[i][j];
                }
            }
        }

        for (const block of this.model.blocks) {
            const normed = this.layerNorm(x, block.ln1.gamma, block.ln1.beta);
            const attnOut = this.attention(normed, block);

            for (let i = 0; i < seqLen; i++) {
                for (let j = 0; j < dModel; j++) {
                    x[i][j] += attnOut[i][j];
                }
            }

            const normed2 = this.layerNorm(x, block.ln2.gamma, block.ln2.beta);
            const ffnOut = this.feedForward(normed2, block);

            for (let i = 0; i < seqLen; i++) {
                for (let j = 0; j < dModel; j++) {
                    x[i][j] += ffnOut[i][j];
                }
            }
        }

        const finalNormed = this.layerNorm(x, this.model.ln_f.gamma, this.model.ln_f.beta);

        const logits = new Array(seqLen);
        for (let i = 0; i < seqLen; i++) {
            logits[i] = new Float32Array(this.tokenizer.vocab_size);
            for (let j = 0; j < this.tokenizer.vocab_size; j++) {
                let dot = 0;
                for (let k = 0; k < dModel; k++) {
                    dot += finalNormed[i][k] * this.model.embedding.weight[j][k];
                }
                logits[i][j] = dot;
            }
        }

        return logits;
    }

    generate(prompt, maxNewTokens = 50, temperature = 0.8, topK = 40) {
        if (!this.ready) {
            return prompt + " [Model not loaded]";
        }

        let tokens = this.encode(prompt);

        for (let i = 0; i < maxNewTokens; i++) {
            const context = tokens.slice(-this.model.config.max_seq_len);

            const logits = this.forward(context);
            const lastLogits = logits[logits.length - 1];

            let scaled = Array.from(lastLogits).map(l => l / temperature);

            // Top-K filtering
            if (topK > 0 && topK < scaled.length) {
                const indexed = scaled.map((v, i) => ({ v, i }));
                indexed.sort((a, b) => b.v - a.v);
                const threshold = indexed[topK]?.v ?? -Infinity;

                for (let j = 0; j < scaled.length; j++) {
                    if (scaled[j] < threshold) {
                        scaled[j] = -Infinity;
                    }
                }
            }

            const probs = this.softmax(scaled);

            const r = Math.random();
            let cumSum = 0;
            let nextToken = 0;

            for (let j = 0; j < probs.length; j++) {
                cumSum += probs[j];
                if (r < cumSum) {
                    nextToken = j;
                    break;
                }
            }

            tokens.push(nextToken);
        }

        return this.decode(tokens);
    }
}

window.NeuralLLM = NeuralLLM;
