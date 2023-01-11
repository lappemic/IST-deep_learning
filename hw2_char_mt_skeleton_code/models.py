import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence as pack
from torch.nn.utils.rnn import pad_packed_sequence as unpack


def reshape_state(state):
    h_state = state[0]
    c_state = state[1]
    new_h_state = torch.cat([h_state[:-1], h_state[1:]], dim=2)
    new_c_state = torch.cat([c_state[:-1], c_state[1:]], dim=2)
    return (new_h_state, new_c_state)


class Attention(nn.Module):
    def __init__(
        self,
        hidden_size,
    ):

        super(Attention, self).__init__()
        "Luong et al. general attention (https://arxiv.org/pdf/1508.04025.pdf)"
        self.linear_in = nn.Linear(hidden_size, hidden_size, bias=False)
        self.linear_out = nn.Linear(hidden_size * 2, hidden_size)

    def forward(
        self,
        query,
        encoder_outputs,
        src_lengths,
    ):
        # query: (batch_size, 1, hidden_dim)
        # encoder_outputs: (batch_size, max_src_len, hidden_dim)
        # src_lengths: (batch_size)
        # we will need to use this mask to assign float("-inf") in the attention scores
        # of the padding tokens (such that the output of the softmax is 0 in those positions)
        # Tip: use torch.masked_fill to do this
        # src_seq_mask: (batch_size, max_src_len)
        # the "~" is the elementwise NOT operator
        src_seq_mask = ~self.sequence_mask(src_lengths)
        #############################################
        # TODO: Implement the forward pass of the attention layer
        # Hints:
        # - Use torch.bmm to do the batch matrix multiplication
        #    (it does matrix multiplication for each sample in the batch)
        # - Use torch.softmax to do the softmax
        # - Use torch.tanh to do the tanh
        # - Use torch.masked_fill to do the masking of the padding tokens
        #############################################
        # just initially taken from https://github.com/spro/practical-pytorch/blob/master/seq2seq-translation/seq2seq-translation-batched.ipynb
        # to have a starting point (good source look at it ass soon as you get here):
        max_len = encoder_outputs.size(0)
        this_batch_size = encoder_outputs.size(1)

        # Create variable to store attention energies
        attn_energies = Variable(torch.zeros(this_batch_size, max_len)) # B x S

        if USE_CUDA:
            attn_energies = attn_energies.cuda()

        # For each batch of encoder outputs
        for b in range(this_batch_size):
            # Calculate energy for each encoder output
            for i in range(max_len):
                attn_energies[b, i] = self.score(hidden[:, b], encoder_outputs[i, b].unsqueeze(0))
                # self.score is another method in the class in the source where 'general attention' is applied as well!

        # Normalize energies to weights in range 0 to 1, resize to 1 x B x S
        attn_out = F.softmax(attn_energies).unsqueeze(1)
        #############################################
        # END OF YOUR CODE
        #############################################
        # attn_out: (batch_size, 1, hidden_size)
        # TODO: Uncomment the following line when you implement the forward pass
        return attn_out

    def sequence_mask(self, lengths):
        """
        Creates a boolean mask from sequence lengths.
        """
        batch_size = lengths.numel()
        max_len = lengths.max()
        return (
            torch.arange(0, max_len)
            .type_as(lengths)
            .repeat(batch_size, 1)
            .lt(lengths.unsqueeze(1))
        )


class Encoder(nn.Module):
    def __init__(
        self,
        src_vocab_size,
        hidden_size,
        padding_idx,
        dropout,
    ):
        super(Encoder, self).__init__()
        self.hidden_size = hidden_size // 2 # // because the LSTM is bidirectional
        self.dropout = dropout

        self.embedding = nn.Embedding(
            src_vocab_size,
            hidden_size,
            padding_idx=padding_idx,
        )
        self.lstm = nn.LSTM(
            hidden_size,
            self.hidden_size,
            bidirectional=True,
            batch_first=True,
        )
        self.dropout = nn.Dropout(self.dropout)

    def forward(
        self,
        src,
        lengths,
    ):
        # src: (batch_size, max_src_len)
        # lengths: (batch_size)
        #############################################
        # TODO: Implement the forward pass of the encoder
        # Hints:
        # - Use torch.nn.utils.rnn.pack_padded_sequence to pack the padded sequences
        #   (before passing them to the LSTM)
        # - Use torch.nn.utils.rnn.pad_packed_sequence to unpack the packed sequences
        #   (after passing them to the LSTM)
        #############################################
        # print(src.shape)
    
        # Get the embedded representation of the src sequence
        embedded = self.dropout(self.embedding(src))
        # Pack the padded sequences TODO: Check values of batch_first and enforce_sorted! Are they True resp. False correct?
        packed_embedded = nn.utils.rnn.pack_padded_sequence(embedded, 
                                                            lengths, 
                                                            batch_first=True, 
                                                            enforce_sorted=False)
        # Pass the packed sequences through the LSTM
        packed_output, final_hidden = self.lstm(packed_embedded) # TODO: is self.hidden_size needed?
        # Unpack the packed sequences
        enc_output, _ = nn.utils.rnn.pad_packed_sequence(packed_output, batch_first=True)
        enc_output = enc_output[:, :, :self.hidden_size] + enc_output[:, : ,self.hidden_size:] # Sum bidirectional outputs
        # Apply dropout to the output
        enc_output = self.dropout(enc_output)
        print('enc_output.shape after Encoder:', enc_output.shape)
        print('shape of final_hidden 1 and 2 after Encoder:', final_hidden[0].shape, final_hidden[1].shape)
        
        # Remarks for debugging
        # - max_src_len from input (src) and enc_output are equal
        # - enc_output has the right dimensions

        #############################################
        # enc_output: (batch_size, max_src_len, hidden_size)
        # final_hidden: tuple with 2 tensors
        # each tensor is (num_layers * num_directions, batch_size, hidden_size)
        # TODO: Uncomment the following line when you implement the forward pass
        return enc_output, final_hidden


class Decoder(nn.Module):
    def __init__(
        self,
        hidden_size,
        tgt_vocab_size,
        attn,
        padding_idx,
        dropout,
    ):
        super(Decoder, self).__init__()
        self.hidden_size = hidden_size
        self.tgt_vocab_size = tgt_vocab_size
        self.dropout = dropout

        self.embedding = nn.Embedding(
            self.tgt_vocab_size, self.hidden_size, padding_idx=padding_idx
        )

        self.dropout = nn.Dropout(self.dropout)
        self.lstm = nn.LSTM(
            self.hidden_size,
            self.hidden_size,
            batch_first=True,
        )

        self.attn = attn

    def forward(
        self,
        tgt,
        dec_state,
        encoder_outputs,
        src_lengths,
    ):
        # tgt: (batch_size, max_tgt_len)
        # dec_state: tuple with 2 tensors
        # each tensor is (num_layers * num_directions, batch_size, hidden_size)
        # encoder_outputs: (batch_size, max_src_len, hidden_size)
        # src_lengths: (batch_size)
        # bidirectional encoder outputs are concatenated, so we may need to
        # reshape the decoder states to be of size (num_layers, batch_size, 2*hidden_size)
        # if they are of size (num_layers*num_directions, batch_size, hidden_size)
        if dec_state[0].shape[0] == 2:
            dec_state = reshape_state(dec_state)
        #############################################
        # TODO: Implement the forward pass of the decoder
        # Hints:
        # - the input to the decoder is the previous target token,
        #   and the output is the next target token
        # - New token representations should be generated one at a time, given
        #   the previous token representation and the previous decoder state
        # - Add this somewhere in the decoder loop when you implement the attention mechanism in 3.2:
        # if self.attn is not None:
        #     output = self.attn(
        #         output,
        #         encoder_outputs,
        #         src_lengths,
        #     )
        #############################################
        # Get the embedded representation of the tgt sequence
        print('encoder_outputs.size:', encoder_outputs.size())
        print('input tgt.size', tgt.size())
        print('input tgt.size(dim=1)', tgt.size(dim=1))
        if tgt.size(dim=1)>1:
            embedded = self.dropout(self.embedding(tgt))
        else:
            embedded = self.dropout(self.embedding(tgt[: , :-1])) #.view(1, 1, -1)
        print('embedded.shape:', embedded.shape)
        # Initialize the output and attention scores
        outputs = []
        attn_scores = []
        # Loop over the tgt sequence -> TODO use split() from torch -> loop over the columns!!
        print('tgt.shape[1] (max_tgt_len):', tgt.shape[1])
        for t in range(tgt.shape[1]):
            # Get the current input
            # input = embedded[:, t, :].unsqueeze(1)
            input = torch.split(embedded, tgt.shape[0], dim=1)
            print('input.size() after torch.split:', input.size())
            # Pass the input through the LSTM
            output, dec_state = self.lstm(input, dec_state)
            # # If the attention mechanism is provided, compute the attention scores and apply attention to the output
            # if self.attn is not None:
            #     output, attn_score = self.attn(
            #         output,
            #         encoder_outputs,
            #         src_lengths,
            #     )
            #     attn_scores.append(attn_score)
            # Append the output to the outputs list
            output = self.dropout(output)
            outputs.append(output)
        # Concatenate the outputs into a single tensor
        outputs = torch.cat(outputs, dim=1) # TODO: Check if concatination is right here
        print('embedded input:', input.size())
        print('outputs.size:', outputs.size())
        print('output.size:', output.size())
        print('decoder dec_state[0].size', dec_state[0].size())
        print('decoder dec_state[1].size', dec_state[1].size())

        #############################################
        # outputs: (batch_size, max_tgt_len, hidden_size)
        # dec_state: tuple with 2 tensors
        # each tensor is (num_layers, batch_size, hidden_size)
        # TODO: Uncomment the following line when you implement the forward pass
        return outputs, dec_state #, attn_scores


class Seq2Seq(nn.Module):
    def __init__(
        self,
        encoder,
        decoder,
    ):
        super(Seq2Seq, self).__init__()

        self.encoder = encoder
        self.decoder = decoder

        self.generator = nn.Linear(decoder.hidden_size, decoder.tgt_vocab_size)

        self.generator.weight = self.decoder.embedding.weight

    def forward(
        self,
        src,
        src_lengths,
        tgt,
        dec_hidden=None,
    ):

        encoder_outputs, final_enc_state = self.encoder(src, src_lengths)

        if dec_hidden is None:
            dec_hidden = final_enc_state

        output, dec_hidden = self.decoder(
            tgt, dec_hidden, encoder_outputs, src_lengths
        )

        return self.generator(output), dec_hidden
