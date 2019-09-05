"""
cli exposed via flask *function-name

wrap create_app with the @command_line_interface decorator

`export FLASK_APP=cluster` is necessary.

`flask --help` to show available functions

to add another cli write a click.command() function and add the function name into CLICK_COMMANDS (at bottom of file)
"""
import click
from ctwpy.io import make_dir_or_complain, write_all_worksheet, delete_dir
from ctwpy.marker_table import run_pipe
import ctwpy.scanpyapi as ad_obj
import tarfile
import os

@click.command(help="Add a scanpy object to the user file system")
@click.argument('worksheet_name')
@click.argument('scanpy_path')
@click.option('--cluster_name', default="louvain")
@click.option('--celltype_key', default="scorect")
def from_scanpy(worksheet_name, scanpy_path, cluster_name,
                celltype_key=None
):
    print("reading in data...")
    ad = ad_obj.readh5ad(scanpy_path)
    print("Attempt to gather cell type mapping")
    mapping = ad_obj.celltype_mapping(ad, cluster_name, celltype_key)
    print("Mapping preview:", mapping.head())
    use_raw = ad_obj.has_raw(ad)
    xys = ad_obj.get_xys(ad, key="X_umap")

    print("Running marker generation")
    markers_df = run_pipe(ad, cluster_name)

    clustering = ad_obj.get_obs(ad, cluster_name)

    exp = ad_obj.get_expression(ad, use_raw)

    # Make the directory to tar up later.
    make_dir_or_complain(worksheet_name)
    write_all_worksheet(worksheet_name, xys=xys, exp=exp, clustering=clustering, markers=markers_df, celltype=mapping)

    ctw_filename = "%s.ctw.tgz" % worksheet_name
    make_tarfile(ctw_filename, source_dir=worksheet_name)
    delete_dir(worksheet_name)

@click.command(help="Upload a worksheet to the UCSC Cell Atlas")
@click.argument('ctw_path')
@click.argument('credentials_path')
def upload_worksheet(ctw_path, credentials_path):
    from ctwpy.webapi import upload
    from ctwpy.io import read_json
    credentials = read_json(credentials_path)
    upload(None, credentials)


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


@click.command(help="See the keys for observation matrix")
@click.argument('scanpy_path')
def scanpy_obs(scanpy_path):
    ad = ad_obj.readh5ad(scanpy_path)
    print(ad.obs_keys())


@click.command()
def bye():
    click.echo('Bye World!')
