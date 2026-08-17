from os import path
import importlib
from code_generation.code_generation import CodeGenerator

from .constants import ERAS, SCOPES, LEGACY_AVAILABLE_SAMPLES


def resolve_sample_surface(config_module):
    """Resolve (available_samples, default_samples) for a config module.

    Config modules may optionally define AVAILABLE_SAMPLES and/or
    DEFAULT_SAMPLES. If neither is defined (e.g. nmssm_config), both fall
    back to the legacy hardcoded sample list for backward compatibility.
    """
    available = getattr(config_module, "AVAILABLE_SAMPLES", None)
    default = getattr(config_module, "DEFAULT_SAMPLES", None)
    if available is None and default is None:
        return list(LEGACY_AVAILABLE_SAMPLES), list(LEGACY_AVAILABLE_SAMPLES)
    if available is None:
        available = list(default)
    if default is None:
        default = list(available)
    return list(available), list(default)


def run(args):
    analysis_name = "bbtautau"

    ## setup variables
    shifts = set([shift.lower() for shift in args.shifts])
    sample_group = args.sample
    era = args.era
    scopes = list(set([scope.lower() for scope in args.scopes]))

    ## load config
    configname = args.config
    config = importlib.import_module(
        f"analysis_configurations.{analysis_name}.{configname}"
    )

    ## resolve and enforce the config-specific sample/era surface BEFORE
    ## build_config is invoked
    available_samples, _ = resolve_sample_surface(config)
    available_eras = getattr(config, "AVAILABLE_ERAS", ERAS)
    available_scopes = SCOPES
    if era not in available_eras:
        raise ValueError(
            f"Config '{configname}' does not support era '{era}' "
            f"(supported: {available_eras})."
        )
    if sample_group not in available_samples:
        raise ValueError(
            f"Config '{configname}' does not accept sample '{sample_group}' "
            f"(accepted: {available_samples})."
        )

    ## Setting up executable
    executable = f"{configname}_{sample_group}_{era}.cxx"
    args.logger.info(f"Generating code for {sample_group}...")
    args.logger.info(f"Configuration used: {config}")
    args.logger.info(f"Era: {era}")
    args.logger.info(f"Shifts: {shifts}")
    config = config.build_config(
        era,
        sample_group,
        scopes,
        shifts,
        available_samples,
        available_eras,
        available_scopes,
    )
    # create a CodeGenerator object
    generator = CodeGenerator(
        main_template_path=args.template,
        sub_template_path=args.subset_template,
        configuration=config,
        executable_name=f"{configname}_{sample_group}_{era}",
        analysis_name=analysis_name,
        config_name=configname,
        output_folder=args.output,
        threads=args.threads,
    )
    if args.debug == "true":
        generator.debug = True
    # generate the code
    generator.generate_code()

    executable = generator.get_cmake_path()

    # append the executable name to the files.txt file
    # if the file does not exist, create it
    if not path.exists(path.join(args.output, "files.txt")):
        with open(path.join(args.output, "files.txt"), "w") as f:
            f.write(f"{executable}\n")
    else:
        with open(path.join(args.output, "files.txt"), "r+") as f:
            for line in f:
                if executable in line:
                    break
            else:
                f.write(f"{executable}\n")
