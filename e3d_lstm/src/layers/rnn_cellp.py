# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Module for constructing RNN Cells."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import paddle.fluid as fluid


class EideticLSTMCell(object):
    """Eidetic LSTM recurrent network cell.

    Implements the model as described in
    Wang, Yunbo, et al. "Eidetic 3D LSTM: A Model for Video Prediction and
    Beyond.", ICLR (2019). https://openreview.net/pdf?id=B1lKS2AqtX
    """

    def __init__(self,
                 conv_ndims,
                 input_shape,
                 output_channels,
                 kernel_shape,
                 layer_norm=True,
                 norm_gain=1.0,
                 norm_shift=0.0,
                 forget_bias=1.0,
                 name="eidetic_lstm_cell"):
        """Construct EideticLSTMCell.

        Args:
          conv_ndims: Convolution dimensionality (1, 2 or 3).
          input_shape: Shape of the input as int tuple, excluding the batch size.
          output_channels: int, number of output channels of the conv LSTM.
          kernel_shape: Shape of kernel as in tuple (of size 1,2 or 3).
          layer_norm: If `True`, layer normalization will be applied.
          norm_gain: float, The layer normalization gain initial value. If
            `layer_norm` has been set to `False`, this argument will be ignored.
          norm_shift: float, The layer normalization shift initial value. If
            `layer_norm` has been set to `False`, this argument will be ignored.
          forget_bias: Forget bias.
          name: Name of the module.

        Raises:
          ValueError: If `input_shape` is incompatible with `conv_ndims`.
        """
        # super(EideticLSTMCell, self).__init__(name=name)

        if conv_ndims != len(input_shape) - 1:
            raise ValueError("Invalid input_shape {} for conv_ndims={}.".format(
                input_shape, conv_ndims))

        self._conv_ndims = conv_ndims
        self._input_shape = input_shape
        self._output_channels = output_channels
        self._kernel_shape = kernel_shape
        self._layer_norm = layer_norm
        self._norm_gain = norm_gain
        self._norm_shift = norm_shift
        self._forget_bias = forget_bias
        self._layer_name = name

    @property
    def output_size(self):
        return self._output_size

    @property
    def state_size(self):
        return self._state_size

    def _norm(self, inp, scope, dtype=None):
        # shape = inp.get_shape()[-1:]
        normalized = fluid.layers.layer_norm(inp)
        return normalized

    def _attn(self, in_query, in_keys, in_values):
        """3D Self-Attention Block.

        Args:
          in_query: Tensor of shape (b,l,w,h,n).
          in_keys: Tensor of shape (b,attn_length,w,h,n).
          in_values: Tensor of shape (b,attn_length,w,h,n).

        Returns:
          attn: Tensor of shape (b,l,w,h,n).

        Raises:
          ValueError: If any number of dimensions regarding the inputs is not 4 or 5
            or if the corresponding dimension lengths of the inputs are not
            compatible.
        """
        q_shape = in_query.shape
        if len(q_shape) == 4:
            batch = q_shape[0]
            width = q_shape[1]
            height = q_shape[2]
            num_channels = q_shape[3]
        elif len(q_shape) == 5:
            batch = q_shape[0]
            width = q_shape[2]
            height = q_shape[3]
            num_channels = q_shape[4]
        else:
            raise ValueError("Invalid input_shape {} for the query".format(q_shape))

        k_shape = in_keys.shape
        if len(k_shape) != 5:
            raise ValueError("Invalid input_shape {} for the keys".format(k_shape))

        v_shape = in_values.shape
        if len(v_shape) != 5:
            raise ValueError("Invalid input_shape {} for the values".format(v_shape))

        if width != k_shape[2] or height != k_shape[3] or num_channels != k_shape[4]:
            raise ValueError("Invalid input_shape {} and {}, not compatible.".format(
                q_shape, k_shape))
        if width != v_shape[2] or height != v_shape[3] or num_channels != v_shape[4]:
            raise ValueError("Invalid input_shape {} and {}, not compatible.".format(
                q_shape, v_shape))
        if k_shape[2] != v_shape[2] or k_shape[3] != v_shape[3] or k_shape[
            4] != v_shape[4]:
            raise ValueError("Invalid input_shape {} and {}, not compatible.".format(
                k_shape, v_shape))

        query = fluid.layers.reshape(in_query, [batch, -1, num_channels])
        keys = fluid.layers.reshape(in_keys, [batch, -1, num_channels])
        values = fluid.layers.reshape(in_values, [batch, -1, num_channels])
        attn = fluid.layers.matmul(query, keys, False, True)
        attn = fluid.layers.softmax(attn, axis=2)
        attn = fluid.layers.matmul(attn, values, False, False)
        if len(q_shape) == 4:
            attn = fluid.layers.reshape(attn, [batch, width, height, num_channels])
        else:
            attn = fluid.layers.reshape(attn, [batch, -1, width, height, num_channels])
        return attn

    def _conv(self, inputs, output_channels, kernel_shape):
        if self._conv_ndims == 2:
            return fluid.layers.conv2d(
                inputs, output_channels, kernel_shape, padding="same")
        elif self._conv_ndims == 3:
            return fluid.layers.conv3d(
                inputs, output_channels, kernel_shape, padding="same", data_format='NDHWC')

    # NOTE: global_memory is always zero?
    # cell is similar as traditional LSTM, is transported to next layer
    # without much modification compared to hidden state
    def __call__(self, inputs, hidden, cell, global_memory, eidetic_cell):
        new_scope = fluid.Scope()
        with fluid.scope_guard(new_scope):
            # fluid.layers.Print(hidden, message='hidden value: ')
            new_hidden = self._conv(hidden, 4 * self._output_channels,
                                    self._kernel_shape)
            if self._layer_norm:
                new_hidden = self._norm(new_hidden, "hidden")
            i_h, g_h, r_h, o_h = fluid.layers.split(
                new_hidden, 4, -1)

            new_inputs = self._conv(inputs, 7 * self._output_channels,
                                    self._kernel_shape)
            if self._layer_norm:
                new_inputs = self._norm(new_inputs, "inputs")
                i_x, g_x, r_x, o_x, temp_i_x, temp_g_x, temp_f_x = fluid.layers.split(
                    new_inputs, 7, -1)

            i_t = fluid.layers.sigmoid(i_x + i_h)
            r_t = fluid.layers.sigmoid(r_x + r_h)
            g_t = fluid.layers.tanh(g_x + g_h)

            new_cell = cell + self._attn(r_t, eidetic_cell, eidetic_cell)
            new_cell = self._norm(new_cell, "self_attn") + i_t * g_t

            new_global_memory = self._conv(global_memory, 4 * self._output_channels,
                                           self._kernel_shape)

            if self._layer_norm:
                new_global_memory = self._norm(new_global_memory, "global_memory")
                i_m, f_m, g_m, m_m = fluid.layers.split(
                    new_global_memory, 4, -1)

            temp_i_t = fluid.layers.sigmoid(temp_i_x + i_m)
            temp_f_t = fluid.layers.sigmoid(temp_f_x + f_m + self._forget_bias)
            temp_g_t = fluid.layers.tanh(temp_g_x + g_m)
            new_global_memory = temp_f_t * fluid.layers.tanh(m_m) + temp_i_t * temp_g_t

            o_c = self._conv(new_cell, self._output_channels, self._kernel_shape)
            o_m = self._conv(new_global_memory, self._output_channels,
                             self._kernel_shape)

            output_gate = fluid.layers.tanh(o_x + o_h + o_c + o_m)

            memory = fluid.layers.concat([new_cell, new_global_memory], -1)
            memory = self._conv(memory, self._output_channels, 1)

            output = fluid.layers.tanh(memory) * fluid.layers.sigmoid(output_gate)

        return output, new_cell, new_global_memory


class Eidetic2DLSTMCell(EideticLSTMCell):
    """2D Eidetic LSTM recurrent network cell.

    Implements the model as described in
    Wang, Yunbo, et al. "Eidetic 3D LSTM: A Model for Video Prediction and
    Beyond.", ICLR (2019). https://openreview.net/pdf?id=B1lKS2AqtX
    """

    def __init__(self, name="eidetic_2d_lstm_cell", **kwargs):
        """Construct Eidetic2DLSTMCell. See `EideticLSTMCell` for more details."""
        super(Eidetic2DLSTMCell, self).__init__(conv_ndims=2, name=name, **kwargs)


class Eidetic3DLSTMCell(EideticLSTMCell):
    """3D Eidetic LSTM recurrent network cell.

    Implements the model as described in
    Wang, Yunbo, et al. "Eidetic 3D LSTM: A Model for Video Prediction and
    Beyond.", ICLR (2019). https://openreview.net/pdf?id=B1lKS2AqtX
    """

    def __init__(self, name="eidetic_3d_lstm_cell", **kwargs):
        """Construct Eidetic3DLSTMCell. See `EideticLSTMCell` for more details."""
        super(Eidetic3DLSTMCell, self).__init__(conv_ndims=3, name=name, **kwargs)
