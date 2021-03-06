import paddle
from paddle.nn import Conv2D, AvgPool2D, MaxPool2D, Linear, BatchNorm2D
from model import Res3D

class ConvBNLayer(paddle.nn.Layer):
    def __init__(self,
                 num_channels,
                 num_filters,
                 filter_size,
                 stride=1,
                 groups=1,
                 padding=0):
        super(ConvBNLayer, self).__init__()

        self._conv = Conv2D(
            in_channels=num_channels,
            out_channels=num_filters,
            kernel_size=filter_size,
            stride=stride,
            padding=padding,
            groups=groups,
            bias_attr=False)

        self._batch_norm = BatchNorm2D(num_filters)

    def forward(self, inputs):
        y = self._conv(inputs)
        y = paddle.nn.functional.relu(y)
        y = self._batch_norm(y)
        y = paddle.nn.functional.relu(y)
        return y


class Inception(paddle.nn.Layer):
    
    def __init__(self, num_channels, ch1x1, ch3x3reduced, ch3x3, doublech3x3reduced, doublech3x3_1, doublech3x3_2, pool_proj):
        '''
        @Brief
             `Inception` 
 
        @Parameters
            num_channels : channel numbers of input tensor
            ch1x1        : output channel numbers of 1x1 conv
            ch3x3reduced : channel numbers of 1x1 conv before 3x3 conv
            ch3x3        : output channel numbers of 3x3 conv
            doublech3x3reduced : channel numbers of 1x1 conv before the double 3x3 convs
            doublech3x3_1        : output channel numbers of the first 3x3 conv
            doublech3x3_2        : output channel numbers of the second 3x3 conv
            pool_proj    : output channel numbers of 1x1 conv after pool

        @Return
             `Inception` model

        '''

        super(Inception, self).__init__()

        self.branch1 = ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch1x1,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)

        self.branch2 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=ch3x3reduced,
                                    num_filters=ch3x3,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch3 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=doublech3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=doublech3x3reduced,
                                    num_filters=doublech3x3_1,
                                    filter_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=doublech3x3_1,
                                    num_filters=doublech3x3_2,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch4 = paddle.nn.Sequential(
                        AvgPool2D(kernel_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=pool_proj,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)
                        )

    
    
    def forward(self, inputs):
        '''
        @Parameters :
            inputs: input tensor
        '''

        branch1 = self.branch1(inputs)
        branch2 = self.branch2(inputs)
        branch3 = self.branch3(inputs)
        branch4 = self.branch4(inputs)

        outputs = paddle.concat([branch1, branch2, branch3, branch4], axis=1)

        return outputs

class Inception3c(paddle.nn.Layer):
    
    def __init__(self, num_channels, ch3x3reduced, ch3x3, doublech3x3reduced, doublech3x3_1, doublech3x3_2):
        '''
        @Brief
             `Inception3c`
 
        @Parameters
            num_channels : channel numbers of input tensor
            ch3x3reduced : channel numbers of 1x1 conv before 3x3 conv
            ch3x3        : output channel numbers of 3x3 conv
            doublech3x3reduced : channel numbers of 1x1 conv before the double 3x3 convs
            doublech3x3_1        : output channel numbers of the first 3x3 conv
            doublech3x3_2        : output channel numbers of the second 3x3 conv

        @Return
            `Inception_3c` model

        '''

        super(Inception3c, self).__init__()

        self.branch1 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=ch3x3reduced,
                                    num_filters=ch3x3,
                                    filter_size=3,
                                    stride=2,
                                    padding=1)
                        )

        self.branch2 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=doublech3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=doublech3x3reduced,
                                    num_filters=doublech3x3_1,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch3 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=doublech3x3_1,
                                    num_filters=doublech3x3_2,
                                    filter_size=3,
                                    stride=2,
                                    padding=1)
                        )

        self.branch4 = MaxPool2D(kernel_size=3,
                        stride=2,
                        padding=1)
    
    def forward(self, inputs):
        '''
        @Parameters :
            inputs: input tensor
        '''

        branch1 = self.branch1(inputs)
        branch2 = self.branch2(inputs)
        branch3 = self.branch3(branch2)
        branch4 = self.branch4(inputs)
        
        outputs = paddle.concat([branch1, branch3, branch4], axis=1)

        return outputs, branch2


class Inception4e(paddle.nn.Layer):
    
    def __init__(self, num_channels, ch3x3reduced, ch3x3, doublech3x3reduced, doublech3x3_1, doublech3x3_2, pool_proj):
        '''
        @Brief
            `Inception4e`
 
        @Parameters
            num_channels : channel numbers of input tensor
            ch1x1        : output channel numbers of 1x1 conv
            ch3x3reduced : channel numbers of 1x1 conv before 3x3 conv
            ch3x3        : output channel numbers of 3x3 conv
            doublech3x3reduced : channel numbers of 1x1 conv before the double 3x3 convs
            doublech3x3_1        : output channel numbers of the first 3x3 conv
            doublech3x3_2        : output channel numbers of the second 3x3 conv
            pool_proj    : output channel numbers of 1x1 conv after pool

        @Return
            `Inception_4e`

        '''

        super(Inception4e, self).__init__()
        
        self.branch1 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=ch3x3reduced,
                                    num_filters=ch3x3,
                                    filter_size=3,
                                    stride=2,
                                    padding=1)
                        )

        self.branch2 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=doublech3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=doublech3x3reduced,
                                    num_filters=doublech3x3_1,
                                    filter_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=doublech3x3_1,
                                    num_filters=doublech3x3_2,
                                    filter_size=3,
                                    stride=2,
                                    padding=1)
                        )

        self.branch3 = MaxPool2D(kernel_size=3,
                        stride=2,
                        padding=1)


    def forward(self, inputs):
        '''
        @Parameters :
            inputs: input tensor
        '''

        branch1 = self.branch1(inputs)
        branch2 = self.branch2(inputs)
        branch3 = self.branch3(inputs)
        
        outputs = paddle.concat([branch1, branch2, branch3], axis=1)

        return outputs


class Inception5a(paddle.nn.Layer):
    
    def __init__(self, num_channels, ch1x1, ch3x3reduced, ch3x3, doublech3x3reduced, doublech3x3_1, doublech3x3_2, pool_proj):
        '''
        @Brief
            `Inception5a`
 
        @Parameters
            num_channels : channel numbers of input tensor
            ch1x1        : output channel numbers of 1x1 conv
            ch3x3reduced : channel numbers of 1x1 conv before 3x3 conv
            ch3x3        : output channel numbers of 3x3 conv
            doublech3x3reduced : channel numbers of 1x1 conv before the double 3x3 convs
            doublech3x3_1        : output channel numbers of the first 3x3 conv
            doublech3x3_2        : output channel numbers of the second 3x3 conv
            pool_proj    : output channel numbers of 1x1 conv after pool

        @Return
            `Inception_5a` model

        '''

        super(Inception5a, self).__init__()

        self.branch1 = ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch1x1,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)

        self.branch2 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=ch3x3reduced,
                                    num_filters=ch3x3,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch3 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=doublech3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=doublech3x3reduced,
                                    num_filters=doublech3x3_1,
                                    filter_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=doublech3x3_1,
                                    num_filters=doublech3x3_2,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch4 = paddle.nn.Sequential(
                        AvgPool2D(kernel_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=pool_proj,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)
                        )

    def forward(self, inputs):
        '''
        @Parameters :
            inputs: input tensor
        '''

        branch1 = self.branch1(inputs)
        branch2 = self.branch2(inputs)
        branch3 = self.branch3(inputs)
        branch4 = self.branch4(inputs)
        
        outputs = paddle.concat([branch1, branch2, branch3, branch4], axis=1)

        return outputs

class Inception5b(paddle.nn.Layer):
    
    def __init__(self, num_channels, ch1x1, ch3x3reduced, ch3x3, doublech3x3reduced, doublech3x3_1, doublech3x3_2, pool_proj):
        '''
        @Brief
            `Inception5b`
 
        @Parameters
            num_channels : channel numbers of input tensor
            ch1x1        : output channel numbers of 1x1 conv
            ch3x3reduced : channel numbers of 1x1 conv before 3x3 conv
            ch3x3        : output channel numbers of 3x3 conv
            doublech3x3reduced : channel numbers of 1x1 conv before the double 3x3 convs
            doublech3x3_1        : output channel numbers of the first 3x3 conv
            doublech3x3_2        : output channel numbers of the second 3x3 conv
            pool_proj    : output channel numbers of 1x1 conv after pool

        @Return
            `Inception_5b` model

        '''

        super(Inception5b, self).__init__()

        self.branch1 = ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch1x1,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)

        self.branch2 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=ch3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=ch3x3reduced,
                                    num_filters=ch3x3,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch3 = paddle.nn.Sequential(
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=doublech3x3reduced,
                                    filter_size=1,
                                    stride=1,
                                    padding=0),
                        ConvBNLayer(num_channels=doublech3x3reduced,
                                    num_filters=doublech3x3_1,
                                    filter_size=3,
                                    stride=1,
                                    padding=1),
                        ConvBNLayer(num_channels=doublech3x3_1,
                                    num_filters=doublech3x3_2,
                                    filter_size=3,
                                    stride=1,
                                    padding=1)
                        )

        self.branch4 = paddle.nn.Sequential(
                        MaxPool2D(kernel_size=3,
                        stride=1,
                        padding=1),
                        ConvBNLayer(num_channels=num_channels,
                                    num_filters=pool_proj,
                                    filter_size=1,
                                    stride=1,
                                    padding=0)
                        )

    def forward(self, inputs):
        '''
        @Parameters :
            inputs: input tensor
        '''

        branch1 = self.branch1(inputs)
        branch2 = self.branch2(inputs)
        branch3 = self.branch3(inputs)
        branch4 = self.branch4(inputs)
        
        outputs = paddle.concat([branch1, branch2, branch3, branch4], axis=1)

        return outputs

class GoogLeNet(paddle.nn.Layer):

    def __init__(self, class_dim=101, seg_num=24, seglen=1, modality="RGB", weight_devay=None):
        '''
        @Brief:
            `GoogLeNet` model
            input image should be 224 * 224
        @Parameters:
            num_channels : channel numbers of input tensor
            out_dim      : the number of classes for classification
        @Return:
            out          : shape=(X, class_dim)

        >>> import numpy as np
        >>> data = np.ones(shape=(8, 3, 224, 224), dtype=np.float32)
        >>> 
            googlenet = GoogLeNet(class_dim=10)
            data = paddle.to_tensor(data)
            y = googlenet(data)
            print(y.numpy().shape)
        (8, 10)
        ''' 
        self.seg_num = seg_num
        self.seglen = seglen
        self.modality = modality
        self.channels = 3 * self.seglen if self.modality == "RGB" else 2 * self.seglen

        super(GoogLeNet, self).__init__() 

        self.part1_list = paddle.nn.Sequential(
                            ConvBNLayer(num_channels=self.channels,
                                        num_filters=64,
                                        filter_size=7,
                                        stride=2,
                                        padding=3),   
                            MaxPool2D(kernel_size=3,
                                        stride=2,
                                        padding=1),
                        )

        self.part2_list = paddle.nn.Sequential(
                            ConvBNLayer(num_channels=64,
                                        num_filters=64,
                                        filter_size=1,
                                        stride=1,
                                        padding=0), 
                            ConvBNLayer(num_channels=64,
                                        num_filters=192,
                                        filter_size=3,
                                        stride=1,
                                        padding=1),  
                            MaxPool2D(kernel_size=3,
                                        stride=2,
                                        padding=1),
                        )

        ##the values of the two pool_padding layers above  are changed from 0 to 1 in order to comply with 28x28 in the paper。However it is 27x27 in the original Caffe code


        self.googLeNet_part1 = paddle.nn.Sequential(
                                ('part1', self.part1_list), 
                                ('part2', self.part2_list), 
                                ('inception_3a', Inception(192,  64,  64, 64, 64, 96, 96, 32)), 
                                ('inception_3b', Inception(256, 64, 64, 96, 64, 96, 96, 64)), 
                            )

        self.before3d = Inception3c(320, 128, 160, 64, 96, 96)

        self.googLeNet_part2 = paddle.nn.Sequential(
                                ('inception_4a', Inception(576, 224, 64, 96, 96, 128, 128, 128)),
                                ('inception_4b', Inception(576, 192, 96, 128, 96, 128, 128, 128)),
                                ('inception_4c', Inception(576, 160, 128, 160, 128, 160, 160, 128)), 
                                ('inception_4d', Inception(608, 96, 128, 192, 160, 192, 192, 128)), 
                            )


        self.googLeNet_part3 = paddle.nn.Sequential(
                                ('inception_4e', Inception4e(608, 128, 192, 192, 256, 256, 608)), 
                                ('inception_5a', Inception5a(1056, 352, 192, 320, 160, 224, 224, 128)), 
                                ('inception_5b', Inception5b(1024, 352, 192, 320, 192, 224, 224, 128)), 
                                ('AvgPool1', paddle.nn.AdaptiveAvgPool2D(output_size=1)), 
                            )

        self.res3d = Res3D.ResNet3D('resnet', modality='RGB', channels=96) 

        self.out = Linear(in_features=1536,
                          out_features=class_dim,
                          weight_attr=paddle.ParamAttr(
                              initializer=paddle.nn.initializer.XavierNormal()))


        self.out_3d = []

    def forward(self, inputs, label=None):

        inputs = paddle.reshape(inputs, [-1, inputs.shape[2], inputs.shape[3], inputs.shape[4]])

        googLeNet_part1 = self.googLeNet_part1(inputs)


        googleNet_b3d, before3d = self.before3d(googLeNet_part1)


        if len(self.out_3d) == self.seg_num:
            
            self.out_3d[:self.seg_num - 1] = self.out_3d[1:]
            self.out_3d[self.seg_num - 1] = before3d
            self.out_3d[self.seg_num - 2].stop_gradient = True

        else:
            while len(self.out_3d) < self.seg_num:
                self.out_3d.append(before3d)

        y_out_3d = self.out_3d[0]
        for i in range(len(self.out_3d) - 1):
            y_out_3d = paddle.concat(x=[y_out_3d,self.out_3d[i+1]], axis=0)
        y_out_3d = paddle.reshape(y_out_3d, [-1, self.seg_num, y_out_3d.shape[1], y_out_3d.shape[2], y_out_3d.shape[3]])
        y_out_3d = paddle.reshape(y_out_3d, [y_out_3d.shape[0], y_out_3d.shape[2], y_out_3d.shape[1], y_out_3d.shape[3], y_out_3d.shape[4]])
        
        out_final_3d = self.res3d(y_out_3d)

        out_final_3d = paddle.reshape(out_final_3d, [-1, out_final_3d.shape[1]])


        out_final_3d = paddle.nn.functional.dropout(out_final_3d, p=0.5)

        out_final_3d = paddle.reshape(out_final_3d, [-1, self.seg_num, out_final_3d.shape[1]])

        out_final_3d = paddle.mean(out_final_3d, axis=1) 


        googLeNet_part2 = self.googLeNet_part2(googleNet_b3d)


        googLeNet_part3 = self.googLeNet_part3(googLeNet_part2)


        googLeNet_part3 = paddle.nn.functional.dropout(googLeNet_part3, p=0.6)

        out_final_2d = paddle.reshape(googLeNet_part3, [-1, googLeNet_part3.shape[1]])

        out_final_2d = paddle.reshape(out_final_2d, [-1, self.seg_num, out_final_2d.shape[1]])

        out_final_2d = paddle.mean(out_final_2d, axis=1)

        out_final = paddle.concat(x=[out_final_2d,out_final_3d], axis=1)

        out_final = self.out(out_final)

        out_final = paddle.nn.functional.softmax(out_final)
        
        if label is not None:
            acc = paddle.metric.accuracy(input=out_final, label=label)
            return out_final, acc
        else:
            return out_final


if __name__ == '__main__':
    network = GoogLeNet()
    img = paddle.zeros([1, 12, 3, 224, 224])
    outs = network(img)
    print(outs.shape)

