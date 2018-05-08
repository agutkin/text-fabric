We describe a conversion of an [example text](ExampleText) to Text-Fabric.

This is not meant as a recipe, but as a description of the pieces of information
that have to be assembled from the source text, and how to compose that into a
Text-Fabric resource, which is a set of features.

How you turn this insight into an executable program is dependent on how the
source text is encoded and organized. See some
[examples](https://github.com/Dans-labs/text-fabric-data/tree/master/programs).

Analysis
--------

The text is a string with a little bit of structure. Some of that structure
gives us our node types, and other bits give us the features.

### Node types ###

The text is divided into main sections, subsections, paragraphs, and sentences.
The sentences are divided into words by white-space and/or punctuation.

#### Step 1: define slots ####

Make a copy of the text, strip out all headings and split the string on
white-space. We get a sequence of "words". These words may contain punctuation or
other non-alphabetical signs. We do not care for the moment.

The indexes in this sequence, from 1 till the number of "words", are our slots.
Let's say we have *S* of them.

We start constructing a mapping from numbers to node types, called `otype`.

We assign to numbers 1, ... ,*S* the string `word`.

That means, we have now *S* nodes, all of type `word`.

#### Step 2: add higher level nodes ####

For each level of *section*, *subsection* and *paragraph*, make new nodes. Nodes
are numbers, and we start making new nodes directly after *S*.

We have 4 main sections, so we extend the `otype` mapping as follows:

*   *S+1* ~ `section`
*   *S+2* ~ `section`
*   *S+3* ~ `section`
*   *S+4* ~ `section`

Likewise, we have 11 subsections, so we continue extending:

*   *S+5* ~ `subsection`
*   *S+6* ~ `subsection`
*   ...
*   *S+16* ~ `subsection`

We do the same for `paragraph`.

And after that, we break the paragraphs up into sentences (split on `.`), and we
add so many nodes of type `sentence`.

The mapping `otype` is called a *feature* of nodes. Any mapping that assigns
values to nodes, is called a (node-)feature.

### Containment ###

We also have to record which words belong to which nodes. This information takes
the shape of a mapping of nodes to sets of nodes. Or, with a slight twist, we
have to lists pairs of nodes `(n, w)` such that the word `w` "belongs" to the
node `n`.

This is in fact a set of edges (pairs of nodes are edges), and a set of edges is
an *edge feature*. In general it is possible to assign values to pairs of nodes,
but for our containment information we just assign the empty value to every pair
we have in our set.

The edge feature that records the containment of words in nodes, is called
`oslots`.

#### Step 3: map nodes to sets of words ####

For each of the higher level nodes `n` (the ones beyond *S*) we have to
lookup/remember/compute which words `w` belong to it, and put that in the
`oslots` mapping:

*   *S+1* ~ { 1, 2, 3, ... x, ..., y }
*   *S+2* ~ { y+1, y+2, ... } ...
*   *S+5* ~ { 1, 2, 3, ... x }
*   *S+6* ~ { x+1, x+2, ...}
*   ...

### Features ###

Now we have two features, a node feature `otype` and an edge feature `oslots`.
This is merely the skeleton of our text, the *warp* so to speak. It contains the
textual positions, and the information what the meaningful chunks are.

Now it is time to weave the information in.

#### Step 4: the actual text ####

Remember the words with punctuation attached? We can split every word into three
parts:

*   text: the alphabetical characters in between
*   prefix: the non-alphabetical leading characters
*   suffix: the non-alphabetical trailing characters

We can make three node features, `prefix`, `text`, and `suffix`. Remember that
node features are mappings from numbers to values.

Here we go:

*   `prefix[1]` is the prefix of word 1
*   `suffix[1]` is the suffix of word 1
*   `text[1]` is the text of word 1
*   ...

And so for all words.

#### Step 5: more features ####

For the sections and subsections we can make a feature `heading`, in which we
store the headings of those sections.

*   `heading[S+1]` is `Introduction`
*   `heading[S+5]` is `Basic concepts`
*   `heading[S+16]` is `Identity`
*   ...

For paragraphs we can figure out their sequence number within the subsection,
and store that in a feature `number`:

*   `number[p]` is 1 if `p` is the node corresponding to the first paragraph in a
    subsection.

If you want absolute paragraph numbers, you can just add a feature for that:

*   `abs_number[p]` is 23 if `p` is the node corresponding to the 23th paragraph
    in the corpus.

### Metadata ###

You can supply metadata to all node features and edge features. Metadata must be
given as a dictionary, where the keys are the names of the features in your
dataset, and the values are themselves key-value pairs, where the values are
just strings.

You can mention where the source data comes from, who did the conversion, and
you can give a description of the intention of this feature and the shape of its
values.

Later, when you save the whole dataset as TF, Text-Fabric will insert a
`datecreated` key-value.

You can also supply metadata for `''` (the empty key). These key-values will be
added to all other features. Here you can put stuff that pertains to the dataset
as a whole, such as information about decisions that have been taken.

You should also provide some special metadata to the key `otext`. This feature
has no data, only metadata. It is not a node feature, not an edge feature, but a
*config* feature. `otext` is responsible for sectioning and text representation.

If you specify `otext` well, the [T-API](Api#text) can make use of it, so that
you have convenient, generic functions to get at your sections and to serialize
your text in different formats.

#### Step 6: sectioning metadata ####

*   `sectionTypes: 'section,subsection,paragraph'`
*   `sectionFeatures: 'title,title,number'`

This tells Text-Fabric that node type `section` corresponds to section level 1,
`subsection` to level 2, and `paragraph` to level 3. Moreover, Text-Fabric knows
that the heading of sections at level 1 and 2 are in the feature `title`, and
that the heading at level 3 is in the feature `number`.

#### Step 7: text formats ####

*   `fmt:text-orig-plain: '{prefix}{text}{suffix}'`
*   `fmt:text-orig-bare: '{text} '`
*   `fmt:text-orig-angle: ' <{text}> '`

Here you have provided a bunch of text representation formats to Text-Fabric.
The names of those formats are up to you, and the values as well.

If you have a list of word nodes, say `ws`, then a user of your corpus can ask
Text-Fabric:

```python
T.text(ws, fmt='text-orig-plain')
```

This will spit out the full textual representation of those words, including
the non-alphabetical stuff in their prefixes and suffixes.

The second format, `text-orig-bare`, will leave prefix and suffix out.

And if for whatever reason you need to wrap each word in angle brackets, you can
achieve that with `text-orig-angle`.

As an example of how text formats come in handy, have a look at the text formats
that have been designed for Hebrew:

    fmt:lex-orig-full: '{g_lex_utf8} '
    fmt:lex-orig-plain: '{lex_utf8} '
    fmt:lex-trans-full: '{g_lex} '
    fmt:lex-trans-plain: '{lex0} '
    fmt:text-orig-full: '{qere_utf8/g_word_utf8}{qere_trailer_utf8/trailer_utf8}'
    fmt:text-orig-full-ketiv: '{g_word_utf8}{trailer_utf8}'
    fmt:text-orig-plain: '{g_cons_utf8}{trailer_utf8}'
    fmt:text-trans-full: '{qere/g_word}{qere_trailer/trailer}'
    fmt:text-trans-full-ketiv: '{g_word}{trailer}'
    fmt:text-trans-plain: '{g_cons}{trailer}'

Note that the actual text-formats are not baked in into TF, but are supplied by
you, the corpus designer.

### Writing out TF ###

Once you have assembled your features and metadata as data structures in memory,
you can use [`TF.save()`](Api#saving-features) to write out your data as a bunch
of Text-Fabric files.

#### Step 8: invoke TF.save() ####

The call to make is

```python
TF.save(nodeFeatures={}, edgeFeatures={}, metaData={}, module=None)
```

Here you supply for `nodeFeatures` a dictionary keyed by your node feature
names and valued by the feature data of those features.

Likewise for the edge features.

And the metadata you have composed goes into the `metaData` parameter.

Finally, the `module` parameter dictates where on your system the TF-files will
be written.

### First time usage ###

When you start using your new dataset in Text-Fabric, you'll notice that there
is some upfront computation going on. Text-Fabric computes derived data,
especially about the relationships between nodes based on the slots they occupy.
All that information comes from `oslots`. The `oslots` information is very
terse, and using it directly would result in a hefty performance penalty.
Likewise, all feature data will be read from the textual `.tf` files,
represented in memory as a dictionary, and then that dictionary will be
serialized and gzipped into a `.tfx` file in a hidden directory `.tf`. These
`.tfx` files load an order of magnitude faster than the original `.tf` files.
Text-Fabric uses the timestamps of the files to determine whether the `.tfx`
files are outdated and need to be regenerated again.

This whole machinery is invisible to you, the user, except for the delay at
first time use.

### Enriching your corpus ###

Maybe a linguistic friend of yours has a tool to determine the part of speech of
each word in the text.

Using TF itself it is not that hard to create a new feature `pos`, that maps
each word node to the part of speech of that word.

See for example how Cody Kingham
[adds](https://github.com/ETCBC/lingo/blob/master/heads/Heads2TF.ipynb)
the notion of linguistic head to the BHSA
datasource of the Hebrew Bible.

#### Step 9: add the new feature ####

Once you have the feature `pos`, provide a bit of metadata, and call

```python
TF.save(
  nodeFeatures={'pos': posData},
  metaData={'pos': posMetaData},
  module='linguistics',
)
```

You get a TF module consisting of one feature `pos.tf` in the `linguistics`
directory.

Maybe you have more linguistic features to add. You do not have to create those
features alongside the original corpus. It is perfectly possible to leave the
corpus alone in its own GitHub repo, and write your new features in another
repo.

Users can just obtain the corpus and your linguistic module separately. When
they call their Text-Fabric, they can point it to both locations, and
Text-Fabric treats it as one dataset.

#### Step 10: use the new feature ####

The call to [`TF=Fabric()`](Api#importing-and-calling-text-fabric) looks like this

```python
TF = Fabric(locations=[corpusLocation, moduleLocation])
```

All feature files found at these locations are loadable in your session.