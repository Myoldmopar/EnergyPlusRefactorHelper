#include <Data.hh>
#include <UtilityFunctions.hh>

void nothing_to(EnergyPlusData &state, void * see_here) {
    // must error
    ShowSevereError(state, "Something Bad");
    ShowContinueError(state, "Happened Here!");  // error here
    int x = 1;
    ShowContinueError(state, format("It might be this: {} or that: {}",state.data->Node(1).Temp,state.data->CoolVector[x].attributeY));
    ShowFatalError(state, "Can't go on...");
}

namespace Something {
    void anotherFunction(EnergyPlusData &state) {
        if (true) {
            int x = 1;
            ShowSevereError(state, "Something Bad");
        } else {
            ShowWarningError(state, fmt::format("{}{}=\"{}\"", RoutineName, state.dataIPShortCut->cCurrentModuleObject, state.dataIPShortCut->cAlphaArgs(1)));
            ShowContinueError(state, format("{} should be zero when the fuel type is electricity.", state.dataIPShortCut->cNumericFieldNames(10)));
            ShowContinueError(state, "It will be ignored and the simulation continues.");
            thisBoiler.ParasiticFuelCapacity = 0.0;
        }
        // path that has a severe, but no direct fatal
        ShowSevereError(state, format("{}{}: invalid: {}",RoutineName,cCurrentModuleObject,state.dataIPShortCut->cAlphaFieldNames(2)));
        ErrorsFound = true;
    }
}