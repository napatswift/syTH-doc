# syTH document
syTH document is a data generation tool that allows users to synthesize large volumes of documents quickly and easily. The tool is designed to be highly customizable and user-friendly, making it ideal for a wide range of use cases.

## Usage
To use syTH document, you will need to download the code and navigate to the main directory. From there, you can run the `gen.py` script with the appropriate arguments to generate the desired number of samples. The available arguments include:

- `--sample_number`: the number of samples to generate.
- `--copy`: the number of copies to create for each sample.
- `--output_dir`: the directory to store the generated documents.

### Example

Here is an example command to generate 700 samples, make two copies of each sample by augmentation, and store them in the `thvl` directory:

```sh
python gen.py --sample_number 700 --copy 2 --output_dir thvl
```

Once you have generated the documents, you can compress them into a single archive file using the `tar` command. Here is an example command to compress the `thvl` directory into a `tar.gz` file:

```sh
tar -zcvf thvl.tar.gz thvl/*
```

This will create a compressed archive file that you can use for storage or distribution.

```
\c:tableOutline=True,tableOutlineWidth=1,lineHeight=50
\c:paperWidth=1000,paperHeight=1000
```