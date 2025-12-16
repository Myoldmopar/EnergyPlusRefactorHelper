# this file will include an abstract base class for any specific refactor
# it will, for now, also include any example refactor configs
from pathlib import Path
from typing import Type

import spacy
from spacy.tokens import Doc

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_folder import SourceFolder


class RefactorBase:
    @staticmethod
    def base_function_call_visitor(function_call) -> str:
        """
        This is a small helper function that simply takes a function call argument, and rewrites it in a functionally
        equivalent manner, returning that string.

        :param function_call: The FunctionCall instance to operate on
        ;return str: The function call in a functionally equivalent string
        """
        return function_call.rewrite()

    @staticmethod
    def base_function_group_visitor(function_group) -> str:
        individual_call_strings = []
        for i, function in enumerate(function_group.function_calls):
            full_call = function.rewrite()
            include_prefix = len(function_group.function_calls) > 0 and i > 0
            including_prefix = (function.preceding_text + full_call) if include_prefix else full_call
            individual_call_strings.append(including_prefix)
        return '\n'.join(individual_call_strings)

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool, skip_plots: bool) -> int:
        raise NotImplementedError()


class ErrorCallRefactor(RefactorBase):
    """
    This is a specific derived refactor class focused on error calls.  Some of the virtual methods have been overridden
    and have their own description below.
    """

    class CallSymbols:
        ShowFatalError = 0
        ShowSevereError = 1
        ShowSevereMessage = 2
        ShowContinueError = 3
        ShowWarningError = 6

    class NewErrorCodes:
        error_code_unclassified = "ErrorMessageCategory::Unclassified"
        error_code_input_invalid = "ErrorMessageCategory::Input_invalid"
        error_code_input_field_not_found = "ErrorMessageCategory::Input_field_not_found"
        error_code_input_field_blank = "ErrorMessageCategory::Input_field_blank"
        error_code_input_object_not_found = "ErrorMessageCategory::Input_object_not_found"
        error_code_input_cannot_find_object = "ErrorMessageCategory::Input_cannot_find_object"  # after input, no index
        error_code_input_topology_problem = "ErrorMessageCategory::Input_topology_problem"
        error_code_input_unused = "ErrorMessageCategory::Input_unused,"
        error_code_input_fatal = "ErrorMessageCategory::Input_fatal"
        error_code_runtime_general = "ErrorMessageCategory::Runtime_general"
        error_code_runtime_flow_out_of_range = "ErrorMessageCategory::Runtime_flow_out_of_range"
        error_code_runtime_temp_out_of_range = "ErrorMessageCategory::Runtime_temp_out_of_range"
        error_code_runtime_airflow_network = "ErrorMessageCategory::Runtime_airflow_network"
        error_code_fatal_general = "ErrorMessageCategory::Fatal_general"
        error_code_developer_general = "ErrorMessageCategory::Developer_general"
        error_code_developer_invalid_index = "ErrorMessageCategory::Developer_invalid_index"

    def __init__(self):
        super().__init__()
        self.matched_error_codes = 0
        self.missed_error_codes = 0
        self.nlp = spacy.load("en_core_web_md")
        self.known_codes = [
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}=\"{}\" invalid range {}=\"{}\"",cCurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1),state.dataIPShortCut->cAlphaFieldNames(4),state.dataIPShortCut->cAlphaArgs(4)), "..contains values outside of range [0,2000 ppm]."}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}, object. Illegal value for {} has been found.",RoutineName,cCurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1),state.dataIPShortCut->cNumericFieldNames(6)), format("{} must be >= 0 or <= 1, entered value = {:.2R}",state.dataIPShortCut->cNumericFieldNames(6),state.dataIPShortCut->rNumericArgs(6))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("Invalid {} = {}", state.dataIPShortCut->cAlphaFieldNames(7), state.dataIPShortCut->cAlphaArgs(7)), format("Entered in {} = {}", state.dataIPShortCut->cCurrentModuleObject, thisWEq.Name)}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}: Invalid input of {}. The default choice is assigned = NO",state.dataHeatBalMgr->CurrentModuleObject,state.dataIPShortCut->cAlphaFieldNames(1)));'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetCoilAirFlowRateVariableSpeed: Could not find CoilType=\"{}\" with Name=\"{}\"", CoilType, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\"", RoutineName, CurrentModuleObject, WalkIn(WalkInID).Name), format("Error found in {} = {}", cAlphaFieldNames(AlphaNum), Alphas(AlphaNum)), "schedule values must be (>=0., <=1.)"}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", {}, maximum is < 0.0", RoutineName, elecEqModuleObject, IHGAlphas(1), IHGAlphaFieldNames(3)), format("Schedule=\"{}\". Maximum is [{:.1R}]. Values must be >= 0.0.", IHGAlphas(3), SchMax)}, false); 😊 emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", {}, maximum is < 0.0", RoutineName, contamSSModuleObject, IHGAlphas(1), IHGAlphaFieldNames(3)), format("Schedule=\"{}\". Maximum is [{:.1R}]. Values must be >= 0.0.", IHGAlphas(3), SchMax)}, false); 😊 1.0000000761785992'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{} statement = {} must have {} between -100C and 100C",RoutineName,cCurrentModuleObject,cAlphaArgs(1),cNumericFieldNames(14)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{} = \"{}\" invalid {} = \"{}\" not found.", cFaultCurrentObject, cAlphaArgs(1), cAlphaFieldNames(6), cAlphaArgs(6)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", invalid entry.", RoutineName, cCurrentModuleObject, cAlphaArgs(1)), format("Missing entry for {}", cAlphaFieldNames(9))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetCoilAirFlowRateVariableSpeed: Could not find CoilType=\"{}\" with Name=\"{}\"", CoilType, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("GetCurveInput: For {}: ", CurrentModuleObject), format("{} [{:.R2}] > {} [{.R2}]",state.dataIPShortCut->cNumericFieldNames(9),Numbers(9),state.dataIPShortCut->cNumericFieldNames(10),Numbers(10))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}=\"{}\", invalid Air Loop specified:",cSetPointManagerType,state.dataSetPointManager->WarmestSetPtMgr(SetPtMgrNum).Name), format("Air Loop not found =\"{}\".", state.dataSetPointManager->WarmestSetPtMgr(SetPtMgrNum).AirLoopName)}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}=\"{}\" invalid {}=[{:.0R}] must be greater than zero.",CurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1),cNumericFields(4),rNumericArgs(4)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", invalid {}, value  [<0.0]={:.3R}",RoutineName,stmEqModuleObject,IHGAlphas(1),IHGNumericFieldNames(3),IHGNumbers(3)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", {} not found=\"{}\".",RoutineName,cCurrentModuleObject,cAlphaArgs(1),cAlphaFieldNames(8),cAlphaArgs(8)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}=\"{}\" invalid {}=\"{}\" not found.", CurrentModuleObject, AlphArray(1), cAlphaFields(8), AlphArray(8)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitWarningMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", {} was lower than the allowable minimum.",RoutineName,cCMO_CoolingPanel_Simple,state.dataIPShortCut->cAlphaArgs(1),state.dataIPShortCut->cNumericFieldNames(11)), format("...reset to minimum value=[{:.3R}].", MinFraction)});'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", invalid {} entered=\"{}\".",RoutineName,peopleModuleObject,IHGAlphas(1),IHGAlphaFieldNames(11),IHGAlphas(11)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}=\"{}\", invalid {}=\"{}\".",cCurrentModuleObject,state.dataSurfaceGeometry->SurfaceTmp(SurfNum).Name,state.dataIPShortCut->cAlphaFieldNames(3),state.dataIPShortCut->cAlphaArgs(3)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", invalid", RoutineName, CurrentModuleObject, thisDXCoil.Name), format("...not found {}=\"{}\".", cAlphaFields(14 + (I - 1) * 6), Alphas(14 + (I - 1) * 6))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitWarningMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", invalid", RoutineName, CurrentModuleObject, thisDXCoil.Name), format("...{} = {} has out of range value.", cAlphaFields(9), Alphas(9)), format("...Curve maximum must be <= 1.0, curve max at PLR = {:.2T} is {:.3T}", MaxCurvePLR, MaxCurveVal), "...Setting curve maximum to 1.0 and simulation continues."});'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitWarningMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", curve values",RoutineName,CurrentModuleObject,state.dataVariableSpeedCoils->VarSpeedCoil(DXCoilNum).Name), format("...{} output is not equal to 1.0 (+ or - 10%) at rated conditions.", cAlphaFields(11)), format("...Curve output at rated conditions = {:.3T}", CurveVal)});'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(m_state, ErrorMessageCategory::Unclassified, {format(RoutineName) + CurrentModuleObject + " object, " + cAlphaFields(6) +" not found = " + OccupantVentilationControl(i).ClosingProbSchName, "..for specified " + cAlphaFields(1) + " = " + Alphas(1)}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", {} must be input ", RoutineName, CurrentModuleObject, WalkIn(WalkInID).Name, cNumericFieldNames(2)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}=\"{}\", invalid Air Loop specified:",cSetPointManagerType,state.dataSetPointManager->WarmestSetPtMgrTempFlow(SetPtMgrNum).Name), format("Air Loop not found =\"{}\".", state.dataSetPointManager->WarmestSetPtMgrTempFlow(SetPtMgrNum).AirLoopName)}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{} {}=\"{}\" is defined as an R-only value material.", cHAMTObject2, cAlphaFieldNames(1), AlphaArray(1)));'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}=\"{}\", no AirLoopHVAC objects found:",cSetPointManagerType,state.dataSetPointManager->RABFlowSetPtMgr(SetPtMgrNum).Name), "Setpoint Manager needs an AirLoopHVAC to operate."}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", invalid {}, value  [<0.0]={:.3R}",RoutineName,peopleModuleObject,thisPeople.Name,IHGNumericFieldNames(2),IHGNumbers(2)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("SimSysAvailManager: AvailabilityManager:ScheduledOff not found: {}", SysAvailName), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}, named {}, PerPerson mode needs positive value input for storage capacity per person",state.dataIPShortCut->cCurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", {} is required.", RoutineName, stmEqModuleObject, thisStmEqInput.Name, IHGAlphaFieldNames(3)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", {} is required.", RoutineName, peopleModuleObject, IHGAlphas(1), IHGAlphaFieldNames(3)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{} = \"{}\", invalid data for \"{}\", entered value <= 0.0, but must be > 0 ",cCurrentModuleObject,AlphArray(1),cNumericFieldNames(3)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", Sum of Fractions > 1.0", RoutineName, lightsModuleObject, thisLights.Name), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_invalid
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", invalid", RoutineName, cCurrentModuleObject, cAlphaArgs(1)), format("not found: {}=\"{}\".", cAlphaFieldNames(5), cAlphaArgs(5))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_not_found
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", invalid", RoutineName, cCurrentModuleObject, cAlphaArgs(1)), format("not found: {}=\"{}\".", cAlphaFieldNames(5), cAlphaArgs(5))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_not_found
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{} not found: {}", cAlphaFields(9), Alphas(9)), format("Occurs in {} = {}", CurrentModuleObject, Alphas(1))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_not_found
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\"", RoutineName, state.dataIPShortCut->cCurrentModuleObject, state.dataIPShortCut->cAlphaArgs(1)), format("{} is blank.", state.dataIPShortCut->cAlphaFieldNames(8))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}\", missing", RoutineName, CurrentModuleObject, thisDXCoil.Name), format("...required {} is blank.", cAlphaFields(16 + (I - 1) * 6))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}=\"{}\" invalid {} is blank and must be entered.", CurrentModuleObject, ventSlab.Name, cAlphaFields(20)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\" {} must be specified.",RoutineName,CurrentModuleObject,Secondary(SecondaryNum).Name,cNumericFieldNames(4)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", {} specifies {}, but that field is blank.  0 Cross Mixing will result.",RoutineName,cCurrentModuleObject,thisMixingInput.Name,cAlphaFieldNames(4),cNumericFieldNames(1)));'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}{}=\"{}\", specifies {}, but that field is blank.  0 Lights will result.",RoutineName,lightsModuleObject,IHGAlphas(1),IHGNumericFieldNames(1)));'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}=\"{}\" invalid {} is required but input is blank.",CurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1),cNumericFields(8)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_blank
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}, GetTESCoilAirInletNode: TES Cooling Coil not found={}", CurrentModuleObject, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_object_not_found
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("{}{}=\"{}, object. Referenced Matrix:TwoDimension is missing from the input file.",RoutineName,locCurrentModuleObject,locAlphaArgs(1)), format("Visble back reflectance Matrix:TwoDimension = \"{}\" is missing from the input file.", locAlphaArgs(9))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_object_not_found
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("AirLoopHVAC:SupplyPlenum=\"{}\", duplicate entry.", state.dataZonePlenum->ZoneSupPlenCond(Count1).ZonePlenumName), format("already exists on AirLoopHVAC:SupplyPath=\"{}\".", FoundNames(Count1))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_topology_problem
            ),
            (
                self.nlp('emitErrorMessages(state, ErrorMessageCategory::Unclassified, {format("AirLoopHVAC:ReturnPlenum=\"{}\", duplicate entry.", state.dataZonePlenum->ZoneRetPlenCond(Count1).ZonePlenumName), format("already exists on AirLoopHVAC:ReturnPath=\"{}\".", FoundNames(Count1))}, false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_topology_problem
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetCoilMaxWaterFlowRate: Could not find CoilType=\"{}\" with Name=\"{}\"", CoilType, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_cannot_find_object
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetInletNodeNum: Could not find EvaporativeCooler = \"{}\"", EvapCondName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_cannot_find_object
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetCoilSteamInletNode: Could not find CoilType=\"{}\" with Name=\"{}\"", CoilType, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_cannot_find_object
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetCoilWaterInletNode: Could not find Coil, Type=\"{}\" Name=\"{}\"", CoilType, CoilName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_cannot_find_object
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("GetFanOutletNode: Could not find Fan, Type=\"{}\" Name=\"{}\"", FanType, FanName), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_cannot_find_object
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}: Refrigeration:AirChiller=\"{}\" unused. ", RoutineName, WarehouseCoil(CoilNum).Name));'),  # noqa: E501
                self.NewErrorCodes.error_code_input_unused
            ),
            (
                self.nlp('emitErrorMessage(m_state, ErrorMessageCategory::Unclassified, format("{}Errors found getting inputs. Previous error(s) cause program termination.", RoutineName), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_fatal
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}Errors found in getting {} input. Preceding condition(s) causes termination.", RoutineName, CurrentModuleObject), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_fatal
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{} = {}:  {} not found = {}",state.dataIPShortCut->cCurrentModuleObject,state.dataIPShortCut->cAlphaArgs(1),state.dataIPShortCut->cAlphaFieldNames(2),state.dataIPShortCut->cAlphaArgs(2)), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_input_field_not_found
            ),
            (
                self.nlp('emitWarningMessages(state, ErrorMessageCategory::Unclassified, {format("{} - air flow rate = {:.7T} in {} = {} is less than the ",CurrentModuleObject,thisCBVAV.FanVolFlow,cAlphaFields(11),thisCBVAV.FanName) +cNumericFields(1), format(" {} is reset to the fan flow rate and the simulation continues.", cNumericFields(1)), format(" Occurs in {} = {}", CurrentModuleObject, thisCBVAV.Name)});'),  # noqa: E501
                self.NewErrorCodes.error_code_runtime_flow_out_of_range
            ),
            (
                self.nlp('ShowSevereError(state, format("CalcElectricEIRChillerModel: Condenser flow = 0, for ElectricEIRChiller={}", this->Name)); ShowContinueErrorTimeStamp(state, "");'),  # noqa: E501
                self.NewErrorCodes.error_code_runtime_flow_out_of_range
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}:\"{}\", {} is less than 2 deg C. Freezing could occur.",cCurrentModuleObject,tower.Name,state.dataIPShortCut->cNumericFieldNames(26)));'),  # noqa: E501
                self.NewErrorCodes.error_code_runtime_temp_out_of_range
            ),
            (
                self.nlp('emitWarningMessage(state, ErrorMessageCategory::Unclassified, format("{}:\"{}\", {} is less than 2 deg C. Freezing could occur.",state.dataIPShortCut->cCurrentModuleObject,thisChiller.Name,state.dataIPShortCut->cNumericFieldNames(30)));'),  # noqa: E501
                self.NewErrorCodes.error_code_runtime_temp_out_of_range
            ),
            (
                self.nlp('emitErrorMessage(m_state, ErrorMessageCategory::Unclassified, "CalcAirflowNetworkMoisBalance: A diagonal entity is zero in AirflowNetwork matrix at node " +AirflowNetworkNodeData(i).Name, true);'),  # noqa: E501
                self.NewErrorCodes.error_code_runtime_airflow_network
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, "SimPipes: Program terminated due to previous condition(s).", true);'),  # noqa: E501
                self.NewErrorCodes.error_code_fatal_general
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, "Preceding condition causes termination.", true);'),  # noqa: E501
                self.NewErrorCodes.error_code_fatal_general
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}: Program terminated due to previous condition(s).", RoutineName), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_fatal_general
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, "InitBaseboard: Program terminated for previous conditions.", true);'),  # noqa: E501
                self.NewErrorCodes.error_code_fatal_general
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("{}: Somehow getNumObjectsFound was > 0 but epJSON.find found 0", cCurrentModuleObject), false);'),  # noqa: E501
                self.NewErrorCodes.error_code_developer_general
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("SimElectricBaseboard:  Invalid CompIndex passed={}, Number of Units={}, Entered Unit name={}",BaseboardNum,numBaseboards,EquipName), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_developer_invalid_index
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, format("InitializeIHP: Invalid CompIndex passed={}, Number of Integrated HPs={}, IHP name=AS-IHP",DXCoilNum,state.dataIntegratedHP->IntegratedHeatPumps.size()), true);'),  # noqa: E501
                self.NewErrorCodes.error_code_developer_invalid_index
            ),
            (
                self.nlp('emitErrorMessage(state, ErrorMessageCategory::Unclassified, "ScheduleAnnualFullLoadHours called with ScheduleIndex out of range", true);'),  # noqa: E501
                self.NewErrorCodes.error_code_developer_invalid_index
            ),
        ]

    @staticmethod
    def function_calls() -> list[str]:
        """
        This method returns all the error functions we want to match during this refactor.

        :return: A list of error function names
        """
        return [
            "ShowFatalError",
            "ShowSevereError",
            "ShowSevereMessage",
            "ShowContinueError",
            "ShowContinueErrorTimeStamp",
            "ShowMessage",
            "ShowWarningError",
            "ShowWarningMessage",
            "ShowRecurringSevereErrorAtEnd",
            "ShowRecurringWarningErrorAtEnd",
            "ShowRecurringContinueErrorAtEnd",
            "StoreRecurringErrorMessage",
            # "ShowErrorMessage",  not in the public interface anymore
            "SummarizeErrors",
            "ShowRecurringErrors",
            "ShowSevereDuplicateName",
            "ShowSevereItemNotFound",
            "ShowSevereInvalidKey",
            "ShowSevereInvalidBool",
            "ShowSevereEmptyField",
            "ShowWarningInvalidKey",
            "ShowWarningInvalidBool",
            "ShowWarningEmptyField",
            "ShowWarningItemNotFound"
        ]

    def visitor(self, function_group) -> str:
        """
        For this action class, this function will be visited for each function call "group".  This function will assess
        the function group, looking for different ways to rewrite the group as a new string.  For right now, this will
        simply iterate over the function group as a whole and rewrite each function call on a new line.  This allows for
        a nice quick test where we can re-apply Clang Format and get back nearly identical code.  In upcoming versions,
        this function will instead group multiple function calls into a single new interface with the messages passed as
        an initializer-list-based array of strings, and also a (for now) dummy error code.  In the final version, this
        will write correct error codes.

        :param function_group: The FunctionCallGroup to inspect, and from that, generate a new string representation.
        :return: A string representation of the function call group.
        """
        if any([f.preceding_text != "" for f in function_group.function_calls]):
            # if there is meaningful text in the group, outside the function calls themselves, just ignore this group
            return RefactorBase.base_function_group_visitor(function_group)
        else:
            # get some convenience variables
            one_liner = len(function_group.function_calls) == 1
            first_call = function_group.function_calls[0]
            last_call = function_group.function_calls[-1]
            middle_calls = function_group.function_calls[1:-1]
            # Look for specific opportunities to refactor.  Let's start with a severe + [N>=0 continue error] + fatal.
            starts_with_fatal = first_call.call_type == self.CallSymbols.ShowFatalError
            starts_with_severe = first_call.call_type == self.CallSymbols.ShowSevereError
            starts_with_warning = first_call.call_type == self.CallSymbols.ShowWarningError
            ends_with_fatal = last_call.call_type == self.CallSymbols.ShowFatalError
            ends_with_continue = last_call.call_type == self.CallSymbols.ShowContinueError
            if len(function_group.function_calls) <= 2:
                valid_middle = True
            else:
                valid_middle = all([f.call_type == self.CallSymbols.ShowContinueError for f in middle_calls])
            state = function_group.function_calls[0].parse_arguments()[0]
            remaining_arguments = [f.parse_arguments()[1] for f in function_group.function_calls]
            argument_one = function_group.function_calls[0].parse_arguments()[1]
            argument_listing = "{" + ", ".join(remaining_arguments) + "}"
            # regroup the errors into a single function call, with a default error code for now

            def text(code: str = "ErrorMessageCategory::Unclassified") -> str:
                if starts_with_severe and valid_middle and ends_with_fatal:
                    return f"emitErrorMessages({state}, {code}, {argument_listing}, true);"
                elif starts_with_severe and valid_middle and ends_with_continue:
                    return f"emitErrorMessages({state}, {code}, {argument_listing}, false);"
                elif starts_with_warning and valid_middle and ends_with_continue:
                    return f"emitWarningMessages({state}, {code}, {argument_listing});"
                elif one_liner and starts_with_warning:
                    return f"emitWarningMessage({state}, {code}, {argument_one});"
                elif one_liner and starts_with_severe:
                    return f"emitErrorMessage({state}, {code}, {argument_one}, false);"
                elif one_liner and starts_with_fatal:
                    return f"emitErrorMessage({state}, {code}, {argument_one}, true);"
                else:
                    return RefactorBase.base_function_group_visitor(function_group)

            unclassified_text = text()
            potential_error_code = self.get_error_code(self.nlp(unclassified_text))
            if potential_error_code == self.NewErrorCodes.error_code_unclassified:
                return unclassified_text
            elif starts_with_warning and potential_error_code == self.NewErrorCodes.error_code_input_fatal:
                # warnings cannot be fatal, so return unclassified
                return unclassified_text
            else:
                return text(potential_error_code)

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool, skip_plots: bool) -> int:
        """This method performs the actual run operations based on input arguments for the error call action.
        This is similar to the base class run() method, but with some specializations.  For example, this run() method
        gathers the error calls into a special structure where we can find similarities and lookup meaningful grouping
        information.

        :param source_repo: The root of the EnergyPlus repository to operate upon.
        :param output_path: An output directory where logs and results should be dumped.
        :param edit_in_place: A flag for whether we are actually editing the repository files in place.  If not, then
                              this will mostly just result in analysis, with outputs in the output_path provided.
        :param skip_plots: A flag for whether to skip plot generation, which can be time-consuming.
        :return: A status flag, 0 if successful, 1 if not.
        """
        root_path = source_repo / 'src' / 'EnergyPlus'
        source_folder = SourceFolder(root_path, self.function_calls())
        matched_source_files = source_folder.find_files(['UtilityRoutines.cc'])
        processed_source_files = source_folder.analyze_source_files(matched_source_files)
        unmatched_err_msg_texts = []
        for source_file in processed_source_files:
            for group in source_file.found_function_groups:
                new_group_text = self.visitor(group)
                if str(self.NewErrorCodes.error_code_unclassified) in new_group_text:
                    self.missed_error_codes += 1
                    unmatched_err_msg_texts.append(new_group_text.replace('\n', ' '))
                else:
                    self.matched_error_codes += 1
        logger.terminal_progress_done()
        # with open('/tmp/output.txt', 'w') as f:
        #     for i in unmatched_err_msg_texts:
        #         f.write(i + '\n')
        source_folder.generate_reports(processed_source_files, output_path, skip_plots=skip_plots)
        if edit_in_place:  # pragma: no cover
            # the rewrite files in place method is already being tested, not including it in coverage here
            source_folder.rewrite_files_in_place(processed_source_files, self.visitor, True)
        logger.log(
            f"Training resulted in {self.matched_error_codes} matched codes and {self.missed_error_codes} missed codes"
        )
        return 0 if source_folder.success else 1

    def get_error_code(self, error_message_spacy_doc: Doc) -> str:
        high_score = 0
        high_score_index = -1
        for i, x in enumerate(self.known_codes):
            doc, code_number = x
            score = error_message_spacy_doc.similarity(doc)
            if score > high_score:
                high_score = score
                high_score_index = i
        if high_score > 0.9:
            return self.known_codes[high_score_index][1]
        return self.NewErrorCodes.error_code_unclassified


all_actions: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}
