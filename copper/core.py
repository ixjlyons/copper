class PipelineBlock(object):

    def __init__(self, name=None, hooks=None):
        self._name = name
        if name is None:
            self._name = self.__class__.__name__

        self._hooks = hooks
        if hooks is None:
            self._hooks = []

    def process(self, data):
        out = data
        return out

    def clear(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def hooks(self):
        return self._hooks

    def __repr__(self):
        return "%s.%s()" % (
            self.__class__.__module__,
            self.__class__.__name__
        )


class Pipeline(PipelineBlock):
    """
    Container for processing a set of PipelineBlock objects arranged in a
    block diagram structure.

    To create a pipeline, the following two rules are needed: blocks in a list
    processed in series, and blocks in a tuple are processed in parallel.

    For example, the following feeds incoming data first to block `a`, and the
    output of block `a` is passed to both blocks `b` and `c`. The output of
    blocks `b` and `c` are then both passed to block `d`.

    >>> from pygesture import pipeline
    >>> a = pipeline.PipelineBlock()
    >>> b = pipeline.PipelineBlock()
    >>> c = pipeline.PipelineBlock()
    >>> d = pipeline.PipelineBlock()
    >>> p = pipeline.Pipeline([a, (b, c), d])

    Blocks that are arranged to take multiple inputs (such as block `d` in the
    above example) should expect to take the corresponding number of inputs in
    the order they are given. It is up to the user constructing the pipeline to
    make sure that the arrangement of blocks makes sense.

    Parameters
    ----------

    blocks : nested lists/tuples of objects derived from PiplineBlock
        The blocks in the pipline, with lists processed in series and tuples
        processed in parallel.

    Attributes
    ----------

    named_blocks : dict
        Dictionary of blocks in the pipeline. Keys are the names given to the
        blocks in the pipeline and values are the block objects.
    """

    def __init__(self, blocks, name=None):
        super(Pipeline, self).__init__(name=name)
        self.blocks = blocks
        self.named_blocks = {}

        # traverse the block structure to fill named_blocks
        self._call_block('name', self.blocks)

    def process(self, data):
        """
        Calls the `process` method of each block in the pipeline, passing the
        outputs around as specified in the block structure.

        Parameters
        ----------
        data : object
            The input to the first block(s) in the pipeline. The type/format
            doesn't matter to copper, as long as the blocks you define accept
            it.

        Returns
        -------
        out : object
            The data output by the `process` method of the last block(s) in the
            pipeline.
        """
        out = self._call_block('process', self.blocks, data)
        return out

    def clear(self):
        """
        Calls the `clear` method on each block in the pipeline. The effect
        depends on the blocks themselves.
        """
        self._call_block('clear', self.blocks)

    def _call_block(self, fname, block, data=None):
        if type(block) is list:
            out = self._call_list(fname, block, data)
        elif type(block) is tuple:
            out = self._call_tuple(fname, block, data)
        else:
            if fname == 'name':
                self.named_blocks[block.name] = block
                return

            f = getattr(block, fname)
            if data is not None:
                out = f(data)
            else:
                out = f()

            if hasattr(block, 'hooks') and fname == 'process':
                for hook in block.hooks:
                    hook(out)

        return out

    def _call_list(self, fname, block, data=None):
        out = data
        for b in block:
            out = self._call_block(fname, b, out)

        return out

    def _call_tuple(self, fname, block, data=None):
        out = []
        for b in block:
            out.append(self._call_block(fname, b, data))

        return out


class PassthroughPipeline(Pipeline):

    def __init__(self, blocks, expand_output=True, name=None):
        super(PassthroughPipeline, self).__init__(blocks, name=name)
        self.expand_output = expand_output

    def process(self, data):
        out = Pipeline.process(self, data)
        if self.expand_output:
            l = [data]
            l.extend(out)
            return l
        else:
            return data, out
